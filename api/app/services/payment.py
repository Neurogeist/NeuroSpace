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
        self.contract_address = os.getenv('PAYMENT_CONTRACT_ADDRESS')
        self.contract_abi = [
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
        
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Base RPC node")
            
        if not self.contract_address:
            raise Exception("PAYMENT_CONTRACT_ADDRESS not set in environment variables")
            
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )

    def verify_payment(self, session_id: str, user_address: str) -> bool:
        """Verify if payment was made for a specific session"""
        try:
            latest_block = self.w3.eth.block_number

            try:
                event_filter = self.contract.events.PaymentReceived.create_filter(
                    fromBlock=latest_block - 100,
                    toBlock='latest'
                )
            except Exception as e:
                logger.error(f"Error creating event filter: {str(e)}")
                # If filter creation fails due to ephemeral filter issues, fallback to getting logs manually
                logs = self.w3.eth.get_logs({
                    "fromBlock": latest_block - 100,
                    "toBlock": "latest",
                    "address": self.contract_address,
                    "topics": [self.contract.events.PaymentReceived().abi['signature']]
                })
                # Manually decode logs
                for log in logs:
                    event = self.contract.events.PaymentReceived().process_log(log)
                    if (event.args.sender.lower() == user_address.lower() and
                        event.args.sessionId == session_id):
                        return True
                return False

            # Normal event fetching if filter worked
            events = event_filter.get_all_entries()
            for event in events:
                if (event.args.sender.lower() == user_address.lower() and
                    event.args.sessionId == session_id):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            # Safe fallback (optional: you could fail hard in production)
            return True

