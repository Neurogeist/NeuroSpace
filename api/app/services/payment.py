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

            try:
                event_filter = self.eth_contract.events.PaymentReceived.create_filter(
                    fromBlock=latest_block - 100,
                    toBlock='latest'
                )
            except Exception as e:
                logger.error(f"Error creating ETH event filter: {str(e)}")
                # Fallback to manual log fetching
                logs = self.w3.eth.get_logs({
                    "fromBlock": latest_block - 100,
                    "toBlock": "latest",
                    "address": self.eth_contract_address,
                    "topics": [self.eth_contract.events.PaymentReceived().abi['signature']]
                })
                for log in logs:
                    event = self.eth_contract.events.PaymentReceived().process_log(log)
                    if (event.args.sender.lower() == user_address.lower() and
                        event.args.sessionId == session_id):
                        return True
                return False

            events = event_filter.get_all_entries()
            for event in events:
                if (event.args.sender.lower() == user_address.lower() and
                    event.args.sessionId == session_id):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error verifying ETH payment: {str(e)}")
            return False

    def _verify_neurocoin_payment(self, session_id: str, user_address: str) -> bool:
        """Verify NeuroCoin payment"""
        try:
            latest_block = self.w3.eth.block_number

            try:
                event_filter = self.neurocoin_contract.events.PaymentReceived.create_filter(
                    fromBlock=latest_block - 100,
                    toBlock='latest'
                )
            except Exception as e:
                logger.error(f"Error creating NeuroCoin event filter: {str(e)}")
                # Fallback to manual log fetching
                logs = self.w3.eth.get_logs({
                    "fromBlock": latest_block - 100,
                    "toBlock": "latest",
                    "address": self.neurocoin_contract_address,
                    "topics": [self.neurocoin_contract.events.PaymentReceived().abi['signature']]
                })
                for log in logs:
                    event = self.neurocoin_contract.events.PaymentReceived().process_log(log)
                    if (event.args.sender.lower() == user_address.lower() and
                        event.args.sessionId == session_id):
                        return True
                return False

            events = event_filter.get_all_entries()
            for event in events:
                if (event.args.sender.lower() == user_address.lower() and
                    event.args.sessionId == session_id):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error verifying NeuroCoin payment: {str(e)}")
            return False

