from web3 import Web3
from eth_account import Account
import hashlib
from typing import Optional
from ..core.config import get_settings

settings = get_settings()

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BASE_RPC_URL))
        
        # Debug logging
        print(f"Private key length: {len(settings.PRIVATE_KEY)}")
        print(f"Private key starts with 0x: {settings.PRIVATE_KEY.startswith('0x')}")
        
        # Handle private key format
        private_key = settings.PRIVATE_KEY
        if private_key.startswith('0x'):
            private_key = private_key[2:]  # Remove '0x' prefix if present
            print(f"Removed 0x prefix, new length: {len(private_key)}")
            
        # Validate private key length (should be 64 characters for 32 bytes)
        if len(private_key) != 64:
            raise ValueError(f"Invalid private key length. Expected 64 characters (32 bytes), got {len(private_key)}")
            
        try:
            self.account = Account.from_key(private_key)
            print(f"Successfully loaded account: {self.account.address}")
        except Exception as e:
            print(f"Error loading account: {str(e)}")
            raise ValueError(f"Failed to load account from private key: {str(e)}")
        
    def hash_prompt(self, prompt: str, response: str, timestamp: str, user_address: Optional[str] = None) -> str:
        """Create a SHA-256 hash of the prompt and response data."""
        data = f"{prompt}{response}{timestamp}{user_address or ''}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def submit_hash(self, prompt_hash: str) -> str:
        """Submit the hash to the Base chain."""
        # Get the current gas price
        gas_price = self.w3.eth.gas_price
        
        # Create a transaction with the hash in the data field
        transaction = {
            'from': self.account.address,
            'to': self.account.address,  # Sending to self as a no-op
            'value': 0,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,  # Increased gas limit
            'maxFeePerGas': gas_price * 2,  # Maximum fee per gas
            'maxPriorityFeePerGas': gas_price,  # Priority fee per gas
            'chainId': 84532,  # Base Goerli chain ID
            'data': self.w3.to_hex(prompt_hash.encode())[:2] + prompt_hash  # Ensure proper hex format
        }
        
        # Sign and send the transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt['transactionHash'].hex() 