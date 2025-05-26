"""
On-Chain Question Answering Agent

This agent handles natural language questions about on-chain data,
performs the necessary queries, and maintains a verifiable execution trace.
"""
import logging
import hashlib
import json
from datetime import datetime
from typing import Any, Dict
import os
import openai
from openai import OpenAI
from web3 import Web3
from web3.exceptions import ContractLogicError
from web3.middleware import geth_poa_middleware

from .base import BaseAgent, ExecutionStep, ExecutionTrace
from ..services.ipfs import IPFSService

logger = logging.getLogger(__name__)

# Rule-based known queries
KNOWN_QUERIES = {
    "what is the total supply of neurocoin": {
        "contract_address": "0x8Cb45bf3ECC760AEC9b4F575FB351Ad197580Ea3",
        "function": "totalSupply",
        "args": [],
        "abi_type": "ERC20"
    }
}

# LLM setup
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """You are a blockchain assistant. Convert the user question into this JSON format:
{
  "contract_address": "0x...",
  "function": "totalSupply",
  "args": [],
  "abi_type": "ERC20"
}
Only return valid JSON. No comments or text outside the JSON block."""

# Minimal ERC-20 ABI for common functions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

class OnChainQAAgent(BaseAgent):
    """Agent for answering questions about on-chain data."""
    
    def __init__(self, agent_id: str, web3_provider: str):
        super().__init__(agent_id)
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        
        # Add middleware for Base (PoS) compatibility
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Verify connection
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to Web3 provider: {web3_provider}")
            
        self.ipfs_service = IPFSService()
    
    async def execute(self, question: str) -> Dict[str, Any]:
        """
        Execute the question answering process.
        
        Args:
            question: Natural language question about on-chain data
            
        Returns:
            Dict containing the answer and execution trace information
        """
        try:
            # Log the question parsing step
            parsed_query = await self._parse_question(question)
            await self.log_step(
                action="parse_question",
                inputs={"question": question},
                outputs={"parsed_query": parsed_query},
                metadata={}
            )
            
            # Execute the query
            result = await self._execute_query(parsed_query)
            await self.log_step(
                action="execute_query",
                inputs={"parsed_query": parsed_query},
                outputs={"result": result},
                metadata={}
            )
            
            # Format the answer
            answer = await self._format_answer(result)
            await self.log_step(
                action="format_answer",
                inputs={"result": result},
                outputs={"answer": answer},
                metadata={}
            )
            
            # Finalize trace and get commitment
            commitment_hash = await self.finalize_trace()
            
            # Store trace on IPFS
            ipfs_hash = await self.store_trace()
            
            return {
                "answer": answer,
                "trace_id": self.current_trace.trace_id,
                "ipfs_hash": ipfs_hash,
                "commitment_hash": commitment_hash,
                "trace_metadata": self.current_trace.to_serializable_dict()
            }
            
        except Exception as e:
            # Log the error
            await self.log_step(
                action="error",
                inputs={"question": question},
                outputs={"error": str(e)},
                metadata={}
            )
            raise
    
    async def _parse_question(self, question: str) -> Dict[str, any]:
        """Parse question using rule-based matching and fallback to LLM if needed."""
        try:
            q_lower = question.lower().strip()

            # Rule-based matching
            if q_lower in KNOWN_QUERIES:
                logger.info(f"Matched known query: {q_lower}")
                return KNOWN_QUERIES[q_lower]

            # Fallback to LLM
            logger.info("Falling back to LLM-based parsing")

            client = OpenAI()
            
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ],
                temperature=0
            )
            content = completion.choices[0].message.content

            parsed = json.loads(content)

            # Validate keys
            required_keys = {"contract_address", "function", "args", "abi_type"}
            if not required_keys.issubset(parsed):
                raise ValueError("Missing one or more required keys in parsed output")

            # Reject placeholder values
            if parsed["contract_address"].strip() == "0x...":
                raise ValueError("LLM returned placeholder contract address (0x...).")

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse question: {e}")
            raise ValueError("Could not parse the question into a structured query")
    
    async def _execute_query(self, parsed_query: Dict[str, Any]) -> Any:
        """
        Execute the parsed query against the blockchain.
        
        Args:
            parsed_query: Dictionary containing contract address, function name,
                        arguments, and ABI type
                        
        Returns:
            The result of the contract function call, adjusted for decimals if needed
            
        Raises:
            ValueError: If the ABI type is not supported
            Exception: For other contract interaction errors
        """
        try:
            contract_address = parsed_query["contract_address"]
            function_name = parsed_query["function"]
            args = parsed_query["args"]
            abi_type = parsed_query["abi_type"]

            if not self.web3.is_address(contract_address):
                raise ValueError(f"Invalid contract address: {contract_address}")

            if abi_type == "ERC20":
                abi = ERC20_ABI
            else:
                raise ValueError(f"Unsupported ABI type: {abi_type}")

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(contract_address),
                abi=abi
            )

            try:
                contract_function = getattr(contract.functions, function_name)
                result = contract_function(*args).call()
            except ContractLogicError as e:
                raise ValueError(f"Contract function call failed: {str(e)}")

            # If function is `totalSupply`, adjust by decimals
            if function_name == "totalSupply":
                try:
                    decimals = contract.functions.decimals().call()
                    human_readable_result = result / (10 ** decimals)
                    logger.info(
                        f"{function_name} (raw): {result}, decimals: {decimals}, adjusted: {human_readable_result}"
                    )
                    return human_readable_result
                except ContractLogicError as e:
                    logger.warning(f"Failed to get decimals, returning raw result: {str(e)}")
                    return result

            logger.info(
                f"Successfully called {function_name} on contract {contract_address} with args {args}. Result: {result}"
            )

            return result

        except ValueError as e:
            logger.error(f"Validation error in _execute_query: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error executing contract query: {str(e)}")
            raise Exception(f"Failed to execute contract query: {str(e)}")

    
    async def _format_answer(self, result: Any) -> str:
        """
        Format the query result into a human-readable answer.
        
        Args:
            result: The raw result from the contract call
            
        Returns:
            str: A human-readable formatted answer
            
        Examples:
            >>> _format_answer(1000000)
            "1,000,000"
            >>> _format_answer("USDC")
            "USDC"
            >>> _format_answer({"name": "USD Coin", "symbol": "USDC"})
            '{\n  "name": "USD Coin",\n  "symbol": "USDC"\n}'
        """
        try:
            if isinstance(result, int) or isinstance(result, float):
            # Format numbers with commas (integers or floats)
                return f"{result:,.0f}" if result == int(result) else f"{result:,.2f}"
            elif isinstance(result, str):
                # Return strings as-is
                return result
            elif isinstance(result, (dict, list)):
                # Format complex objects as pretty-printed JSON
                return json.dumps(result, indent=2)
            else:
                # For any other type, convert to string
                return str(result)
                
        except Exception as e:
            logger.error(f"Error formatting answer: {str(e)}")
            # Fallback to string representation if formatting fails
            return str(result)
    
    async def store_trace(self) -> str:
        """
        Store the execution trace on IPFS.
        
        Returns:
            str: The IPFS hash (CID) of the stored trace
            
        Raises:
            ValueError: If there is no current trace to store
            Exception: If there is an error storing the trace on IPFS
        """
        if not self.current_trace:
            raise ValueError("No trace to store")
            
        try:
            # Convert trace to serializable dictionary
            trace_data = self.current_trace.to_serializable_dict()
            
            # Upload to IPFS
            ipfs_hash = await self.ipfs_service.upload_json(trace_data)
            
            # Update the trace with the IPFS hash
            self.current_trace.ipfs_hash = ipfs_hash
            
            logger.info(f"Successfully stored trace on IPFS with hash: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Failed to store trace on IPFS: {str(e)}")
            raise Exception(f"Failed to store trace on IPFS: {str(e)}")
    
    async def submit_commitment(self, ipfs_hash: str) -> str:
        """
        Submit the commitment hash and IPFS hash for verification.
        
        This is a placeholder implementation that simulates a successful submission.
        In the future, this will be replaced with actual on-chain submission via web3.py.
        
        Args:
            ipfs_hash: The IPFS hash (CID) of the stored trace
            
        Returns:
            str: A simulated transaction hash
            
        Raises:
            ValueError: If there is no current trace or commitment hash
        """
        if not self.current_trace or not self.current_trace.commitment_hash:
            raise ValueError("No trace or commitment hash available")
            
        commitment_hash = self.current_trace.commitment_hash
        
        # Log the submission
        logger.info(
            f"Submitting commitment hash {commitment_hash} with IPFS hash {ipfs_hash}"
        )
        
        # Simulate a successful submission by generating a fake transaction hash
        # This is just a hash of the concatenated hashes for demonstration
        fake_tx_hash = hashlib.sha256(
            f"{commitment_hash}{ipfs_hash}".encode()
        ).hexdigest()
        
        # Format as a fake Ethereum transaction hash
        simulated_tx_hash = f"0x{fake_tx_hash[:40]}"
        
        logger.info(f"Simulated transaction hash: {simulated_tx_hash}")
        return simulated_tx_hash 