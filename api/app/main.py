from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
import base58
import json
from typing import Optional, Dict
import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import uuid
import asyncio
from datetime import datetime
import logging
import borsh_construct as borsh
from .solana_utils import (
    create_prompt_account,
    create_submit_prompt_instruction,
    submit_transaction,
    Keypair
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="NeuroChain API")

# Initialize Solana client
solana_client = Client(os.getenv("SOLANA_RPC_URL", "http://localhost:8899"))

# Load program ID from environment or use a default
PROGRAM_ID = Pubkey.from_string(os.getenv("PROGRAM_ID", "EYRgrzQXVT5m2WENS9FtFuq3rS8nFkba9Rs6pkuXcFri"))

# Constants for account sizing
DISCRIMINATOR_SIZE = 8  # Size of the account discriminator
PUBKEY_SIZE = 32  # Size of a public key
BOOL_SIZE = 1  # Size of a boolean
STRING_LENGTH_SIZE = 4  # Size of string length prefix
MAX_PROMPT_SIZE = 1000  # Maximum size for prompt text
MAX_RESPONSE_SIZE = 2000  # Maximum size for response text
TIMESTAMP_SIZE = 8  # Size of timestamp (u64)

# Calculate total account size
ACCOUNT_SIZE = (
    DISCRIMINATOR_SIZE +
    PUBKEY_SIZE +  # owner
    BOOL_SIZE +  # is_processed
    STRING_LENGTH_SIZE + MAX_PROMPT_SIZE +  # prompt
    STRING_LENGTH_SIZE + MAX_RESPONSE_SIZE +  # response
    TIMESTAMP_SIZE  # created_at
)

# Load model and tokenizer
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# In-memory storage for development
prompts: Dict[str, Dict] = {}

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    prompt_id: str
    prompt: str
    response: Optional[str]
    is_processed: bool
    account_address: Optional[str]
    transaction_signature: Optional[str]

def serialize_instruction(prompt: str) -> bytes:
    """Serialize the instruction data using Borsh."""
    try:
        # Create a buffer for the serialized data
        buffer = bytearray()
        
        # Write the variant (0 for SubmitPrompt)
        buffer.extend(borsh.U8.build(0))
        
        # Write the string length and string data
        prompt_bytes = prompt.encode('utf-8')
        buffer.extend(borsh.U32.build(len(prompt_bytes)))
        buffer.extend(prompt_bytes)
        
        return bytes(buffer)
    except Exception as e:
        raise Exception(f"Error serializing instruction: {str(e)}")

async def get_minimum_rent() -> int:
    """Get the minimum rent for an account of our size."""
    try:
        # Get the minimum rent for our account size
        rent = solana_client.get_minimum_balance_for_rent_exemption(ACCOUNT_SIZE)
        return rent.value
    except Exception as e:
        logger.error(f"Error getting minimum rent: {str(e)}")
        raise

async def create_prompt_account(prompt: str) -> tuple[Pubkey, list[Instruction], Keypair]:
    """Create a new account for storing the prompt, returning instructions and keypair."""
    try:
        # Generate a new keypair for the account
        account_keypair = Keypair()

        # Get minimum rent
        rent = await get_minimum_rent()

        # Create account instruction
        create_account_ix = Instruction(
            program_id=SYS_PROGRAM_ID,
            data=bytes([0]),  # Create account instruction
            accounts=[
                AccountMeta(
                    pubkey=account_keypair.pubkey(),
                    is_signer=True,
                    is_writable=True
                ),
                AccountMeta(
                    pubkey=PROGRAM_ID,
                    is_signer=False,
                    is_writable=False
                ),
            ],
        )

        # Create compute budget instructions
        compute_limit_ix = set_compute_unit_limit(200_000)
        compute_price_ix = set_compute_unit_price(1)

        # Return the instructions and keypair
        return account_keypair.pubkey(), [compute_limit_ix, compute_price_ix, create_account_ix], account_keypair
    except Exception as e:
        logger.error(f"Error creating prompt account: {str(e)}")
        raise

def create_submit_prompt_instruction(prompt: str, account_pubkey: Pubkey) -> Instruction:
    """Create a SubmitPrompt instruction."""
    try:
        # Serialize the instruction data
        serialized_data = serialize_instruction(prompt)

        # Create the instruction
        return Instruction(
            program_id=PROGRAM_ID,
            data=serialized_data,
            accounts=[
                AccountMeta(
                    pubkey=account_pubkey,
                    is_signer=True,
                    is_writable=True
                ),
            ],
        )
    except Exception as e:
        logger.error(f"Error creating submit prompt instruction: {str(e)}")
        raise

async def submit_transaction(transaction: Transaction, keypair: Keypair) -> str:
    """Submit a transaction to the Solana network."""
    try:
        # Sign the transaction
        transaction.sign([keypair])
        
        # Send the transaction
        result = solana_client.send_transaction(transaction)
        
        if result.value.err:
            raise Exception(f"Transaction failed: {result.value.err}")
            
        return str(result.value)
    except Exception as e:
        logger.error(f"Error submitting transaction: {str(e)}")
        raise

@app.post("/prompts", response_model=PromptResponse)
async def submit_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    try:
        # Create new account for the prompt
        account_pubkey, create_account_instructions, account_keypair = await create_prompt_account(request.prompt)

        # Create the submit prompt instruction
        submit_prompt_ix = create_submit_prompt_instruction(request.prompt, account_pubkey)

        # Get recent blockhash
        recent_blockhash = solana_client.get_latest_blockhash().value.blockhash

        # Create a new transaction with all instructions
        transaction = Transaction.new_with_payer(
            instructions=create_account_instructions + [submit_prompt_ix],
            payer=account_pubkey
        )

        # Set the blockhash
        transaction.set_blockhash(recent_blockhash)

        # Generate a unique ID for tracking
        prompt_id = str(uuid.uuid4())

        # Store the prompt in memory
        prompts[prompt_id] = {
            "prompt": request.prompt,
            "response": None,
            "is_processed": False,
            "account_address": str(account_pubkey),
            "created_at": datetime.utcnow().isoformat()
        }

        # Submit the transaction
        transaction_signature = await submit_transaction(transaction, account_keypair)

        return PromptResponse(
            prompt_id=prompt_id,
            prompt=request.prompt,
            response=None,
            is_processed=False,
            account_address=str(account_pubkey),
            transaction_signature=transaction_signature
        )
    except Exception as e:
        logger.error(f"Error in submit_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get the status of a prompt."""
    try:
        if prompt_id not in prompts:
            raise HTTPException(status_code=404, detail="Prompt not found")

        prompt_data = prompts[prompt_id]
        return PromptResponse(
            prompt_id=prompt_id,
            prompt=prompt_data["prompt"],
            response=prompt_data["response"],
            is_processed=prompt_data["is_processed"],
            account_address=prompt_data["account_address"]
        )
    except Exception as e:
        logger.error(f"Error in get_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_prompt_background(prompt_id: str):
    """Background task to process prompts and submit responses."""
    try:
        if prompt_id not in prompts:
            return

        prompt_data = prompts[prompt_id]
        if prompt_data["is_processed"]:
            return

        # Process the prompt
        response = await process_prompt(prompt_data["prompt"])

        # TODO: Calculate hash of model, prompt, and response
        # hash_data = calculate_hash(model, prompt_data["prompt"], response)

        # Submit response to chain
        await submit_response_to_chain(
            prompt_data["account_address"],
            response,
            # hash_data
        )

        # Update local state
        prompts[prompt_id]["response"] = response
        prompts[prompt_id]["is_processed"] = True
        prompts[prompt_id]["processed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.error(f"Error processing prompt {prompt_id}: {str(e)}")
        prompts[prompt_id]["error"] = str(e)

async def submit_response_to_chain(account_address: str, response: str, hash_data: Optional[str] = None):
    """Submit response back to the Solana program."""
    try:
        # For development/testing, just log the response
        logger.info(f"Would submit response to account {account_address}: {response}")
    except Exception as e:
        logger.error(f"Error submitting response to chain: {str(e)}")
        raise

async def process_prompt(prompt: str) -> str:
    """Process the prompt using the loaded model."""
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            inputs["input_ids"],
            max_length=100,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Start background task to monitor for unprocessed prompts
    asyncio.create_task(monitor_unprocessed_prompts())

async def monitor_unprocessed_prompts():
    """Background task to monitor and process unhandled prompts."""
    while True:
        try:
            for prompt_id, prompt_data in prompts.items():
                if not prompt_data["is_processed"]:
                    await process_prompt_background(prompt_id)
            await asyncio.sleep(1)  # Check every second
        except Exception as e:
            logger.error(f"Error in monitor_unprocessed_prompts: {str(e)}")
            await asyncio.sleep(5)  # Wait longer on error

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)