from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from solana.rpc.api import Client
from solana.transaction import Transaction
#from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.signature import Signature
from solders.system_program import transfer, TransferParams
from borsh_construct import Enum as BorshEnum, CStruct, String
import base58
import json
from typing import Optional, Dict
import os
import time
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import uuid
import asyncio
from datetime import datetime
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Custom exceptions
class BlockchainError(Exception):
    """Base exception for blockchain-related errors."""
    pass

class TransactionError(BlockchainError):
    """Exception for transaction-related errors."""
    pass

class AccountError(BlockchainError):
    """Exception for account-related errors."""
    pass

# Initialize FastAPI app
app = FastAPI(title="NeuroChain API")

# Initialize Solana client
solana_client = Client(os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"))

# Load program ID from environment
PROGRAM_ID = Pubkey.from_string(os.getenv("PROGRAM_ID", "YOUR_PROGRAM_ID_HERE"))

# Constants for account sizing
DISCRIMINATOR_SIZE = 8
PUBKEY_SIZE = 32
BOOL_SIZE = 1
STRING_LENGTH_SIZE = 4
MAX_PROMPT_SIZE = 1000
MAX_RESPONSE_SIZE = 2000
TIMESTAMP_SIZE = 8

# Calculate total account size
ACCOUNT_SIZE = (
    DISCRIMINATOR_SIZE +
    PUBKEY_SIZE +
    BOOL_SIZE +
    STRING_LENGTH_SIZE + MAX_PROMPT_SIZE +
    STRING_LENGTH_SIZE + MAX_RESPONSE_SIZE +
    TIMESTAMP_SIZE
)

# Load model and tokenizer
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# In-memory storage for development
prompts: Dict[str, Dict] = {}

def wait_for_airdrop(pubkey: Pubkey, timeout: int = 10):
    logger.info(f"Waiting for airdrop to confirm for {pubkey}...")
    for _ in range(timeout):
        balance = solana_client.get_balance(pubkey).value
        if balance > 0:
            logger.info(f"Airdrop confirmed. Balance: {balance} lamports")
            return
        time.sleep(1)
    raise Exception("Airdrop failed or timed out.")

def request_airdrop_and_wait(pubkey: Pubkey, amount: int = 1_000_000_000, retries: int = 10, delay: int = 1):
    """Request airdrop and wait for confirmation and balance update."""
    try:
        sig = solana_client.request_airdrop(pubkey, amount).value
        logger.info(f"Requested airdrop with signature: {sig}")

        # Confirm the transaction
        confirmed = False
        for i in range(retries):
            status = solana_client.get_signature_statuses([sig])
            if status.value and status.value[0] and status.value[0].confirmation_status == "confirmed":
                confirmed = True
                logger.info(f"Airdrop transaction confirmed.")
                break
            logger.info(f"Waiting for airdrop confirmation... attempt {i + 1}/{retries}")
            time.sleep(delay)

        if not confirmed:
            raise Exception("Airdrop signature not confirmed.")

        # Check balance
        for i in range(retries):
            balance = solana_client.get_balance(pubkey).value
            if balance > 0:
                logger.info(f"Airdrop reflected in balance: {balance} lamports")
                return
            logger.info(f"Waiting for balance... attempt {i + 1}/{retries}")
            time.sleep(delay)

        raise Exception("Airdrop confirmed but balance is still 0.")
    except Exception as e:
        logger.error(f"Airdrop failed: {e}")
        raise

# Load funding keypair from environment or create a new one
def get_or_create_funding_keypair() -> Keypair:
    """Load funding keypair from Solana CLI or from FUNDING_KEYPAIR in env."""
    try:
        # Option 1: FUNDING_KEYPAIR set in .env as base58-encoded private key
        env_key = os.getenv("FUNDING_KEYPAIR")
        if env_key:
            logger.info("Loaded funding keypair from .env FUNDING_KEYPAIR")
            return Keypair.from_bytes(base58.b58decode(env_key))

        # Option 2: Load from Solana CLI default keypair (id.json)
        keypair_path = os.path.expanduser("~/.config/solana/id.json")
        with open(keypair_path, "r") as f:
            secret_key = json.load(f)
        logger.info(f"Loaded funding keypair from {keypair_path}")
        return Keypair.from_bytes(bytes(secret_key))

    except Exception as e:
        logger.error(f"Error loading funding keypair: {str(e)}")
        raise

FUNDING_KEYPAIR = get_or_create_funding_keypair()

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    prompt_id: str
    prompt: str
    response: Optional[str]
    is_processed: bool
    account_address: Optional[str]
    signature: Optional[str]

async def get_minimum_rent() -> int:
    """Get the minimum rent for an account of our size."""
    try:
        rent = solana_client.get_minimum_balance_for_rent_exemption(ACCOUNT_SIZE)
        return rent.value
    except Exception as e:
        logger.error(f"Error getting minimum rent: {str(e)}")
        raise AccountError(f"Failed to get minimum rent: {str(e)}")
    
async def sign_and_send_transaction(transaction: Transaction, *signers: Keypair) -> Signature:
    try:
        recent_blockhash = solana_client.get_latest_blockhash().value.blockhash
        transaction.recent_blockhash = recent_blockhash
        transaction.sign(*signers)  # sign with all required keypairs
        result = solana_client.send_transaction(transaction, *signers)  # also pass all signers

        if result.value is None:
            raise TransactionError("Transaction failed: No signature returned.")
        return result.value
    except Exception as e:
        logger.error(f"Error signing and sending transaction: {str(e)}")
        raise TransactionError(f"Failed to send transaction: {str(e)}")

async def fund_account(account_pubkey: Pubkey, amount: int) -> Signature:
    """Transfer SOL to fund a new account."""
    try:
        # Check funding keypair balance
        balance = solana_client.get_balance(FUNDING_KEYPAIR.pubkey())
        if balance.value < amount:
            # Request airdrop if needed
            try:
                solana_client.request_airdrop(FUNDING_KEYPAIR.pubkey(), amount + 1000000)  # Add extra for fees
                logger.info(f"Requested airdrop for funding keypair")
            except Exception as e:
                logger.warning(f"Could not airdrop to funding keypair: {str(e)}")
        
        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=FUNDING_KEYPAIR.pubkey(),
                to_pubkey=account_pubkey,
                lamports=amount
            )
        )
        
        # Create transaction
        transaction = Transaction()
        transaction.add(transfer_ix)

        
        # Sign and send transaction
        return await sign_and_send_transaction(transaction, FUNDING_KEYPAIR)
    except Exception as e:
        logger.error(f"Error funding account: {str(e)}")
        raise AccountError(f"Failed to fund account: {str(e)}")

async def create_prompt_account(prompt: str) -> tuple[Pubkey, Transaction, Keypair]:
    """Create a new account for storing the prompt."""
    try:
        # Generate a new keypair for the account
        account_keypair = Keypair()
        
        # Get minimum rent
        rent = await get_minimum_rent()
        
        # Fund the account with rent + some extra for transaction fees
        funding_amount = rent + 1000000  # Add 0.001 SOL for fees
        await fund_account(account_keypair.pubkey(), funding_amount)
        
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
        
        # Create transaction
        transaction = Transaction()
        transaction.add(compute_limit_ix, compute_price_ix, create_account_ix)
        
        
        return account_keypair.pubkey(), transaction, account_keypair
    except Exception as e:
        logger.error(f"Error creating prompt account: {str(e)}")
        raise AccountError(f"Failed to create account: {str(e)}")

async def submit_prompt_to_chain(prompt: str, account_pubkey: Pubkey, account_keypair: Keypair) -> str:
    """Submit prompt to the Solana program."""
    try:
        # Create instruction to submit prompt
        from borsh_construct import CStruct, Enum as BorshEnum, String
        from construct import Container

        # Define the enum properly
        PromptInstructionEnum = BorshEnum(
            "SubmitPrompt" / CStruct("prompt" / String),
            "SubmitResponse" / CStruct("response" / String),
            enum_name="PromptInstructionEnum"
        )

        # Build the SubmitPrompt instruction data
        instruction_data = PromptInstructionEnum.build(
            Container(
                SubmitPrompt=Container(
                    prompt=prompt
                )
            )
        )
        
        submit_prompt_ix = Instruction(
            program_id=PROGRAM_ID,
            data=instruction_data,
            accounts=[
                AccountMeta(
                    pubkey=account_pubkey,
                    is_signer=True,
                    is_writable=True
                ),
            ],
        )
        
        # Create compute budget instructions
        compute_limit_ix = set_compute_unit_limit(200_000)
        compute_price_ix = set_compute_unit_price(1)
        
        # Create and send transaction
        transaction = Transaction(fee_payer=FUNDING_KEYPAIR.pubkey())
        transaction.add(compute_limit_ix, compute_price_ix, submit_prompt_ix)
        
        # Sign and send transaction
        return await sign_and_send_transaction(transaction, account_keypair, FUNDING_KEYPAIR)
    except Exception as e:
        logger.error(f"Error submitting prompt to chain: {str(e)}")
        raise TransactionError(f"Failed to submit prompt: {str(e)}")

@app.post("/prompts", response_model=PromptResponse)
async def submit_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    try:
        # Create new account for the prompt
        account_pubkey, transaction, account_keypair = await create_prompt_account(request.prompt)
        
        # Submit prompt to chain
        signature = await submit_prompt_to_chain(request.prompt, account_pubkey, account_keypair)
        
        # Generate a unique ID for tracking
        prompt_id = str(uuid.uuid4())
        
        # Store the prompt in memory
        prompts[prompt_id] = {
            "prompt": request.prompt,
            "response": None,
            "is_processed": False,
            "account_address": str(account_pubkey),
            "created_at": datetime.utcnow().isoformat(),
            "signature": signature
        }
        
        # Add to background tasks for processing
        background_tasks.add_task(process_prompt_background, prompt_id)
        
        return PromptResponse(
            prompt_id=prompt_id,
            prompt=request.prompt,
            response=None,
            is_processed=False,
            account_address=str(account_pubkey),
            signature=signature
        )
    except BlockchainError as e:
        logger.error(f"Blockchain error in submit_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in submit_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
            account_address=prompt_data["account_address"],
            signature=prompt_data.get("signature")
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