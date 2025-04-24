from web3 import Web3
from eth_account import Account
import hashlib
from typing import Optional, Dict, Any
from ..core.config import get_settings
import os
import logging

from eth_account.messages import encode_defunct


logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        self.settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(self.settings.BASE_RPC_URL))
        self.private_key = self.settings.PRIVATE_KEY
        if not self.private_key:
            raise ValueError("PRIVATE_KEY environment variable is not set")
        self.account = Account.from_key(self.private_key)
        self.contract_address = self.settings.CONTRACT_ADDRESS
        self.contract_abi = [
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "_hash",
                        "type": "bytes32"
                    }
                ],
                "name": "storeHash",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "_hash",
                        "type": "bytes32"
                    }
                ],
                "name": "getHashInfo",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "submitter",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "_hash",
                        "type": "bytes32"
                    }
                ],
                "name": "hashExists",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "submitter",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "bytes32",
                        "name": "hash",
                        "type": "bytes32"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    }
                ],
                "name": "HashStored",
                "type": "event"
            }
        ]
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to {self.settings.BLOCKCHAIN_NETWORK} RPC node")
            
        if not self.contract_address:
            raise Exception("CONTRACT_ADDRESS not set in environment variables")
            
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        logger.info(f"Connected to {self.settings.BLOCKCHAIN_NETWORK} network")
        logger.info(f"Using contract address: {self.contract_address}")
        logger.info(f"Account address: {self.account.address}")
        
    def hash_prompt(self, prompt: str, response: str, timestamp: str, user_address: Optional[str] = None) -> str:
        """Create a SHA-256 hash of the prompt and response data."""
        data = f"{prompt}{response}{timestamp}{user_address or ''}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def submit_to_blockchain(self, prompt_hash: str) -> Dict[str, str]:
        """Submit the hash to the blockchain."""
        try:
            # Get the current gas price
            gas_price = self.w3.eth.gas_price
            logger.info(f"Current gas price: {self.w3.from_wei(gas_price, 'gwei')} gwei")
            
            # Convert hash to bytes32
            hash_bytes = Web3.to_bytes(hexstr=prompt_hash)
            
            # Create transaction
            transaction = {
                'from': self.account.address,
                'to': self.contract_address,
                'value': 0,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 100000,  # Increased gas limit
                'maxFeePerGas': gas_price * 2,  # Maximum fee per gas
                'maxPriorityFeePerGas': gas_price,  # Priority fee per gas
                'chainId': self.settings.chain_id,
                'data': self.contract.encodeABI(fn_name='storeHash', args=[hash_bytes])
            }
            
            logger.info(f"Sending transaction from {transaction['from']}")
            logger.info(f"Transaction data: {transaction['data']}")
            
            # Sign and send the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Transaction receipt status: {receipt['status']}")
            logger.info(f"Transaction block number: {receipt['blockNumber']}")
            logger.info(f"View on {self.settings.BLOCKCHAIN_NETWORK}: {self.settings.block_explorer_url}/tx/{receipt['transactionHash'].hex()}")
            
            # Get the event logs
            #logs = self.contract.events.HashStored().process_receipt(receipt)
            #if not logs:
            #    raise Exception("No HashStored event found in transaction receipt")
                
            return {
                'transaction_hash': receipt['transactionHash'].hex(),
                'block_number': str(receipt['blockNumber']),
                'status': 'success' if receipt['status'] == 1 else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Error submitting to blockchain: {str(e)}")
            raise
    
    async def get_hash_info(self, hash_str: str) -> Dict[str, Any]:
        """Get information about a stored hash."""
        try:
            # Convert hash to bytes32
            hash_bytes = Web3.to_bytes(hexstr=hash_str)
            
            # Call the contract
            submitter, timestamp = self.contract.functions.getHashInfo(hash_bytes).call()
            
            return {
                'submitter': submitter,
                'timestamp': timestamp,
                'exists': True
            }
            
        except Exception as e:
            if "Hash does not exist" in str(e):
                return {
                    'exists': False
                }
            logger.error(f"Error getting hash info: {str(e)}")
            raise

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