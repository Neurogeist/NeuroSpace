from web3 import Web3
from typing import Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class PaymentService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
        
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

    def verify_payment(self, session_id: str, user_address: str, payment_method: str = 'ETH') -> bool:
        """Verify if payment was made for a specific session"""
        try:
            if payment_method == 'ETH':
                return self._verify_eth_payment(session_id, user_address)
            elif payment_method == 'NEURO':
                return self._verify_neurocoin_payment(session_id, user_address)
            else:
                logger.error(f"Invalid payment method: {payment_method}")
                return False
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False

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
            logger.info(f"🔍 Verifying NeuroCoin payment for session_id={session_id}, user_address={user_address}")
            
            # Check if contract is paused
            try:
                logger.info("📡 Calling paused()...")
                is_paused = self.neurocoin_contract.functions.paused().call()
                logger.info(f"✅ paused() returned: {is_paused}")
            except Exception as e:
                logger.error(f"🚨 Failed to call paused(): {str(e)}", exc_info=True)
                raise
            
            if is_paused:
                logger.error("🚫 NeuroCoin payment contract is paused")
                return False

            latest_block = self.w3.eth.block_number
            from_block = max(latest_block - 100, 0)
            logger.info(f"🔎 Searching logs from block {from_block} to latest")

            event_signature = self.w3.keccak(text="PaymentReceived(address,uint256,string)").hex()
            logger.info(f"🔑 Event signature: {event_signature}")

            filter_params = {
                "fromBlock": from_block,
                "toBlock": "latest",
                "address": self.neurocoin_contract_address,
                "topics": [event_signature]
            }

            try:
                logs = self.w3.eth.get_logs(filter_params)
                logger.info(f"📦 Found {len(logs)} PaymentReceived logs")

                for log in logs:
                    try:
                        event = self.neurocoin_contract.events.PaymentReceived().process_log(log)
                        logger.info(f"🔍 Checking event: sender={event.args.sender}, sessionId={event.args.sessionId}")

                        if (event.args.sender.lower() == user_address.lower() and
                            event.args.sessionId == session_id):
                            logger.info(f"✅ Found matching payment event for session {session_id}")
                            return True
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing log: {str(e)}", exc_info=True)
                        continue

                logger.warning(f"❌ No matching payment found for session {session_id}")
                return False

            except Exception as e:
                logger.error(f"🚨 Error getting logs: {str(e)}", exc_info=True)
                return False

        except Exception as e:
            logger.error(f"❗ Error verifying NeuroCoin payment: {str(e)}", exc_info=True)
            return False

