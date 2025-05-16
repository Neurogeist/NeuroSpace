from web3 import Web3
from typing import Optional, Dict
import os
from dotenv import load_dotenv
import logging
from ..models.database import SessionLocal
from ..models.free_request import FreeRequest
from sqlalchemy.orm import Session
import redis
import time

logger = logging.getLogger(__name__)
load_dotenv()

class PaymentService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
        
        # Initialize Redis client
        redis_url = os.getenv("REDIS_URL") or os.getenv("RAILWAY_REDIS_URL")
        if redis_url:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            try:
                self.redis_client.ping()
                logger.info("✅ Redis client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")
                self.redis_client = None
        else:
            self.redis_client = None
            logger.warning("No Redis URL provided, falling back to non-atomic verification")
        
        # ETH Payment Contract
        self.eth_contract_address = os.getenv('PAYMENT_CONTRACT_ADDRESS')
        self.eth_contract_abi = [
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "sessionId",
                        "type": "string"
                    }
                ],
                "name": "payForMessage",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "sender",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "sessionId",
                        "type": "string"
                    }
                ],
                "name": "PaymentReceived",
                "type": "event"
            }
        ]
        
        # NeuroCoin Payment Contract
        self.neurocoin_contract_address = os.getenv('NEUROCOIN_PAYMENT_CONTRACT_ADDRESS')
        self.neurocoin_contract_abi = [
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "sessionId",
                        "type": "string"
                    }
                ],
                "name": "payForMessage",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "sender",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "sessionId",
                        "type": "string"
                    }
                ],
                "name": "PaymentReceived",
                "type": "event"
            },
            {
                "inputs": [],
                "name": "pricePerMessage",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "paused",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Base RPC node")
            
        if not self.eth_contract_address:
            raise Exception("PAYMENT_CONTRACT_ADDRESS not set in environment variables")
            
        if not self.neurocoin_contract_address:
            raise Exception("NEUROCOIN_PAYMENT_CONTRACT_ADDRESS not set in environment variables")
            
        self.eth_contract = self.w3.eth.contract(
            address=self.eth_contract_address,
            abi=self.eth_contract_abi
        )
        
        self.neurocoin_contract = self.w3.eth.contract(
            address=self.neurocoin_contract_address,
            abi=self.neurocoin_contract_abi
        )

        logger.info("✅ Payment service initialized")

    def verify_payment(self, session_id: str, user_address: str, payment_method: str = 'ETH') -> bool:
        """Verify if payment was made for a specific session"""
        try:
            # Create a unique lock key for this payment verification
            lock_key = f"payment_verification:{session_id}:{user_address}:{payment_method}"
            
            # Try to acquire lock with Redis if available
            if self.redis_client:
                # Try to set the lock with a 10-second expiration
                acquired = self.redis_client.set(
                    lock_key,
                    "1",
                    ex=10,
                    nx=True  # Only set if key doesn't exist
                )
                
                if not acquired:
                    logger.warning(f"Payment verification already in progress for {session_id}")
                    return False
            
            try:
                # Verify payment based on method
                if payment_method == 'FREE':
                    if self._has_free_request(user_address):
                        logger.info(f"Using free request for user {user_address}")
                        return True
                    logger.error(f"No free requests remaining for user {user_address}")
                    return False
                elif payment_method == 'ETH':
                    return self._verify_eth_payment(session_id, user_address)
                elif payment_method == 'NEURO':
                    return self._verify_neurocoin_payment(session_id, user_address)
                else:
                    logger.error(f"Invalid payment method: {payment_method}")
                    return False
            finally:
                # Release the lock if we have Redis
                if self.redis_client:
                    self.redis_client.delete(lock_key)
                    
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False

    def _has_free_request(self, user_address: str) -> bool:
        """Check if user has free requests and use one if available"""
        user_address = user_address.lower()
        db = SessionLocal()
        
        try:
            # Get or create free request record
            free_request = db.query(FreeRequest).filter(FreeRequest.wallet_address == user_address).first()
            
            if not free_request:
                free_request = FreeRequest(wallet_address=user_address, remaining_requests=10)
                db.add(free_request)
                db.commit()
                logger.info(f"Initialized free requests for new user {user_address}")
            
            # Use a free request if available
            if free_request.remaining_requests > 0:
                free_request.remaining_requests -= 1
                db.commit()
                logger.info(f"Used free request for user {user_address}. {free_request.remaining_requests} remaining")
                return True
                
            logger.info(f"No free requests remaining for user {user_address}")
            return False
            
        except Exception as e:
            logger.error(f"Error managing free request: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_remaining_free_requests(self, user_address: str) -> int:
        """Get the number of remaining free requests for a user"""
        user_address = user_address.lower()
        db = SessionLocal()
        
        try:
            free_request = db.query(FreeRequest).filter(FreeRequest.wallet_address == user_address).first()
            if not free_request:
                # Create new record with 10 free requests
                free_request = FreeRequest(wallet_address=user_address, remaining_requests=10)
                db.add(free_request)
                db.commit()
                return 10
            return free_request.remaining_requests
        except Exception as e:
            logger.error(f"Error getting remaining free requests: {str(e)}")
            db.rollback()
            return 0
        finally:
            db.close()

    def _verify_eth_payment(self, session_id: str, user_address: str) -> bool:
        """Verify ETH payment"""
        try:
            latest_block = self.w3.eth.block_number
            from_block = max(latest_block - 100, 0)  # Ensure we don't go below block 0

            # Get the event signature hash
            event_abi = {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "sender", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "sessionId", "type": "string"}
                ],
                "name": "PaymentReceived",
                "type": "event"
            }
            event_signature = self.w3.keccak(text="PaymentReceived(address,uint256,string)").hex()

            # Create the filter parameters
            filter_params = {
                "fromBlock": from_block,
                "toBlock": "latest",
                "address": self.eth_contract_address,
                "topics": [event_signature]
            }

            try:
                # Try to get logs directly
                logs = self.w3.eth.get_logs(filter_params)
                logger.info(f"Found {len(logs)} ETH payment events")
                
                # Process logs
                for log in logs:
                    try:
                        # Decode the log data using the contract's event interface
                        event = self.eth_contract.events.PaymentReceived().process_log(log)
                        
                        # Check if this is the payment we're looking for
                        if (event.args.sender.lower() == user_address.lower() and
                            event.args.sessionId == session_id):
                            logger.info(f"Found matching ETH payment event for session {session_id}")
                            return True
                    except Exception as e:
                        logger.warning(f"Error processing ETH log: {str(e)}")
                        continue
                
                logger.warning(f"No matching ETH payment found for session {session_id}")
                return False

            except Exception as e:
                logger.error(f"Error getting ETH logs: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Error verifying ETH payment: {str(e)}")
            return False
        
    def _verify_neurocoin_payment(self, session_id: str, user_address: str) -> bool:
        """Verify NeuroCoin payment"""
        try:
            # Check if contract is paused
            try:
                is_paused = self.neurocoin_contract.functions.paused().call()
                if is_paused:
                    logger.error("NeuroCoin payment contract is paused")
                    return False
            except Exception as e:
                logger.warning(f"Failed to check paused status: {str(e)}")
                is_paused = False

            # Get logs from recent blocks
            latest_block = self.w3.eth.block_number
            from_block = max(latest_block - 100, 0)
            
            event_signature = self.w3.keccak(text="PaymentReceived(address,uint256,string)").hex()
            filter_params = {
                "fromBlock": from_block,
                "toBlock": "latest",
                "address": self.neurocoin_contract_address,
                "topics": [event_signature]
            }

            try:
                logs = self.w3.eth.get_logs(filter_params)
                logger.info(f"Found {len(logs)} PaymentReceived logs")

                for log in logs:
                    try:
                        event = self.neurocoin_contract.events.PaymentReceived().process_log(log)
                        if (event.args.sender.lower() == user_address.lower() and
                            event.args.sessionId == session_id):
                            logger.info(f"Found matching payment for session {session_id}")
                            return True
                    except Exception as e:
                        logger.warning(f"Error processing log: {str(e)}")
                        continue

                logger.warning(f"No matching payment found for session {session_id}")
                return False

            except Exception as e:
                logger.error(f"Error getting logs: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Error verifying NeuroCoin payment: {str(e)}")
            return False

