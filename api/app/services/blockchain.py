from web3 import Web3
from eth_account import Account
import hashlib
from typing import Optional
from ..core.config import get_settings
import os
import logging

from eth_account.messages import encode_defunct


logger = logging.getLogger(__name__)

settings = get_settings()

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
        self.private_key = os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("PRIVATE_KEY environment variable is not set")
        self.account = Account.from_key(self.private_key)
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract_abi = [
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "hash",
                        "type": "bytes32"
                    }
                ],
                "name": "storeHash",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
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
    
    async def submit_hash(self, prompt_hash: str) -> str:
        """Submit the hash to the Base chain."""
        try:
            # Get the current gas price
            gas_price = self.w3.eth.gas_price
            print(f"Current gas price: {self.w3.from_wei(gas_price, 'gwei')} gwei")
            
            # Create a transaction with the hash in the data field
            transaction = {
                'from': self.account.address,
                'to': self.account.address,  # Sending to self as a no-op
                'value': 0,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 100000,  # Increased gas limit
                'maxFeePerGas': gas_price * 2,  # Maximum fee per gas
                'maxPriorityFeePerGas': gas_price,  # Priority fee per gas
                'chainId': 84532,  # Base Sepolia chain ID
                'data': self.w3.to_hex(prompt_hash.encode('utf-8'))  # Encode as UTF-8 bytes first
            }
            
            print(f"Sending transaction from {transaction['from']}")
            print(f"Transaction data: {transaction['data']}")
            
            # Sign and send the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction receipt status: {receipt['status']}")
            print(f"Transaction block number: {receipt['blockNumber']}")
            print(f"View on Base Sepolia: https://sepolia.basescan.org/tx/{receipt['transactionHash'].hex()}")
            
            return receipt['transactionHash'].hex()
            
        except Exception as e:
            print(f"Error submitting hash to blockchain: {str(e)}")
            raise Exception(f"Blockchain submission failed: {str(e)}")



    def sign_message(self, message_hash: str) -> str:
        """Sign a message hash with the private key."""
        try:
            # Prepare the message using EIP-191
            message = encode_defunct(hexstr=message_hash)

            # Sign the message
            signed_message = self.account.sign_message(message)

            # Return the hex-encoded signature
            return signed_message.signature.hex()

        except Exception as e:
            logger.error(f"Error signing message: {str(e)}")
            raise

    def submit_to_blockchain(self, hash_value: str) -> dict:
        """
        Submit a hash to the blockchain.
        
        Args:
            hash_value: The hash to submit (hex string)
            
        Returns:
            Dictionary containing transaction details
        """
        try:
            # Convert hex string to bytes32
            hash_bytes = Web3.to_bytes(hexstr=hash_value)
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            logger.info(f"Current gas price: {gas_price / 1e9} gwei")
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            transaction = self.contract.functions.storeHash(hash_bytes).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'to': self.contract_address
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Return transaction details
            return {
                'transaction_hash': tx_hash.hex(),
                'block_number': tx_receipt['blockNumber'],
                'status': tx_receipt['status'],
                'gas_used': tx_receipt['gasUsed'],
                'view_on_basescan': f"https://sepolia.basescan.org/tx/{tx_hash.hex()}"
            }
        except Exception as e:
            logger.error(f"Error submitting to blockchain: {str(e)}")
            raise 

    def verify_signature(self, message_hash: str, signature: str) -> str:
        """Verify a signature and recover the signer's address."""
        try:
            # Prepare the message using EIP-191
            message = encode_defunct(hexstr=message_hash)
            
            # Recover the address from the signature
            recovered_address = self.w3.eth.account.recover_message(
                message,
                signature=signature
            )
            
            return recovered_address
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            raise 