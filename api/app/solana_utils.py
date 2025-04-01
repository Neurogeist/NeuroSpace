from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from solders.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
import borsh_construct as borsh
from typing import Optional
import base58
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Solana client
solana_client = Client(os.getenv("SOLANA_RPC_URL", "http://localhost:8899"))

# Load program ID from environment
PROGRAM_ID = Pubkey.from_string(os.getenv("PROGRAM_ID", "EYRgrzQXVT5m2WENS9FtFuq3rS8nFkba9Rs6pkuXcFri"))

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
    PUBKEY_SIZE +  # owner
    BOOL_SIZE +  # is_processed
    STRING_LENGTH_SIZE + MAX_PROMPT_SIZE +  # prompt
    STRING_LENGTH_SIZE + MAX_RESPONSE_SIZE +  # response
    TIMESTAMP_SIZE  # created_at
)

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
        rent = solana_client.get_minimum_balance_for_rent_exemption(ACCOUNT_SIZE)
        return rent.value
    except Exception as e:
        raise Exception(f"Error getting minimum rent: {str(e)}")

async def create_prompt_account(prompt: str) -> tuple[Pubkey, list[Instruction]]:
    """Create a new account for storing the prompt, returning instructions."""
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
        
        # Return the instructions
        return account_keypair.pubkey(), [compute_limit_ix, compute_price_ix, create_account_ix]
    except Exception as e:
        raise Exception(f"Error creating prompt account: {str(e)}")

def create_submit_prompt_instruction(prompt: str, account_pubkey: Pubkey) -> Instruction:
    """Create a SubmitPrompt instruction."""
    try:
        # Explicit import of serialize_instruction
        from .solana_utils import serialize_instruction
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
        raise Exception(f"Error creating submit prompt instruction: {str(e)}")

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
        raise Exception(f"Error submitting transaction: {str(e)}")