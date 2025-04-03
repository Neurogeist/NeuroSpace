from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def view_transaction(tx_hash: str):
    """View transaction details from Base Goerli."""
    # Connect to Base Goerli
    w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
    
    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    
    # Get transaction details
    tx = w3.eth.get_transaction(tx_hash)
    
    print("\nTransaction Details:")
    print("-" * 50)
    print(f"Transaction Hash: {tx_hash}")
    print(f"Block Number: {receipt['blockNumber']}")
    print(f"From: {tx['from']}")
    print(f"To: {tx['to']}")
    print(f"Gas Used: {receipt['gasUsed']}")
    print(f"Data: {tx['input']}")
    print(f"Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    
    # Get block timestamp
    block = w3.eth.get_block(receipt['blockNumber'])
    print(f"Timestamp: {block['timestamp']}")

if __name__ == "__main__":
    # Example transaction hash from your logs
    tx_hash = "0x674a6ec2fa2b9227fab007746c9c16f2bc8f609975c7dc1b8b0805bb7301fe6b"
    view_transaction(tx_hash) 