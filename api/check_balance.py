from solders.keypair import Keypair
import base58
import os
from dotenv import load_dotenv
from solana.rpc.api import Client
import time

def check_balance():
    # Load environment variables
    load_dotenv()
    
    # Initialize Solana client
    solana_client = Client(os.getenv("SOLANA_RPC_URL", "http://localhost:8899"))
    
    # Load the payer keypair
    payer_private_key = os.getenv("PAYER_PRIVATE_KEY")
    if not payer_private_key:
        raise ValueError("PAYER_PRIVATE_KEY environment variable is not set")
    payer_keypair = Keypair.from_bytes(base58.b58decode(payer_private_key))
    
    # Get the balance
    balance = solana_client.get_balance(payer_keypair.pubkey())
    
    print(f"Payer account: {payer_keypair.pubkey()}")
    print(f"Balance: {balance.value / 1e9} SOL")  # Convert lamports to SOL
    
    # Check recent transactions
    signatures = solana_client.get_signatures_for_address(payer_keypair.pubkey())
    if signatures.value:
        print("\nRecent transactions:")
        for sig in signatures.value:
            tx = solana_client.get_transaction(sig.signature)
            print(f"Signature: {sig.signature}")
            print(f"Status: {tx.value.err}")
            print(f"Block time: {tx.value.block_time}")
            print("---")

if __name__ == "__main__":
    print("Checking balance...")
    check_balance()
    
    print("\nWaiting 5 seconds for any pending transactions...")
    time.sleep(5)
    
    print("\nChecking balance again...")
    check_balance() 