"""
On-Chain Question Answering Agent

This agent handles natural language questions about on-chain data,
performs the necessary queries, and maintains a verifiable execution trace.
"""
import logging
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional
import os
import openai
from openai import OpenAI
from web3 import Web3
from web3.exceptions import ContractLogicError
from web3.middleware import geth_poa_middleware

from .base import BaseAgent, ExecutionStep, ExecutionTrace
from .schemas import OnChainQuery, ERC20_FUNCTIONS, SYSTEM_PROMPT
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
        self.client = OpenAI()
    
    async def execute(self, question: str) -> Dict[str, Any]:
        """
        Execute the question answering process.
        
        Args:
            question: Natural language question about on-chain data
            
        Returns:
            Dict containing the answer and execution trace information
        """
        try:
            # Parse the question
            parsed_query = await self._parse_question(question)
            await self.log_step(
                action="parse_question",
                inputs={"question": question},
                outputs={"parsed_query": parsed_query.dict()},
                metadata={}
            )
            
            # Execute the query
            result = await self._execute_query(parsed_query)
            await self.log_step(
                action="execute_query",
                inputs={"parsed_query": parsed_query.dict()},
                outputs={"result": result},
                metadata={}
            )
            
            # Format the answer
            answer = await self._format_answer(parsed_query, result)
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
    
    async def _parse_question(self, question: str) -> OnChainQuery:
        """
        Parse question using rule-based matching and fallback to LLM if needed.
        
        Args:
            question: Natural language question
            
        Returns:
            OnChainQuery: Structured query object
            
        Raises:
            ValueError: If the question cannot be parsed
        """
        try:
            q_lower = question.lower().strip()

            # Rule-based matching
            if q_lower in KNOWN_QUERIES:
                logger.info(f"Matched known query: {q_lower}")
                return OnChainQuery(**KNOWN_QUERIES[q_lower])

            # Fallback to LLM
            logger.info("Falling back to LLM-based parsing")
            
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ],
                temperature=0
            )
            content = completion.choices[0].message.content

            # Parse and validate the response
            parsed = json.loads(content)
            query = OnChainQuery(**parsed)
            
            # Validate function exists
            if query.function not in ERC20_FUNCTIONS:
                raise ValueError(f"Unsupported function: {query.function}")
                
            # Validate arguments
            function_meta = ERC20_FUNCTIONS[query.function]
            if len(query.args) != len(function_meta.args):
                raise ValueError(
                    f"Function {query.function} expects {len(function_meta.args)} arguments, "
                    f"got {len(query.args)}"
                )

            return query

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("Could not parse the LLM response into a valid query")
        except Exception as e:
            logger.error(f"Failed to parse question: {e}")
            raise ValueError(f"Could not parse the question: {str(e)}")
    
    async def _execute_query(self, query: OnChainQuery) -> Any:
        """
        Execute the parsed query against the blockchain.
        
        Args:
            query: Structured query object
            
        Returns:
            The result of the contract function call
            
        Raises:
            ValueError: If the query is invalid
            Exception: For other contract interaction errors
        """
        try:
            # Get function metadata
            function_meta = ERC20_FUNCTIONS[query.function]
            
            # Create contract instance
            contract = self.web3.eth.contract(
                address=query.contract_address,
                abi=ERC20_ABI
            )

            try:
                # Call the function
                contract_function = getattr(contract.functions, query.function)
                result = contract_function(*query.args).call()
                
                # Apply decimals adjustment if needed
                if function_meta.decimals_adjustment:
                    try:
                        decimals = contract.functions.decimals().call()
                        result = result / (10 ** decimals)
                    except ContractLogicError as e:
                        logger.warning(f"Failed to get decimals, returning raw result: {str(e)}")
                
                return result
                
            except ContractLogicError as e:
                raise ValueError(f"Contract function call failed: {str(e)}")

        except Exception as e:
            logger.error(f"Error executing contract query: {str(e)}")
            raise Exception(f"Failed to execute contract query: {str(e)}")
    
    async def _format_answer(self, query: OnChainQuery, result: Any) -> str:
        """
        Format the query result into a human-readable answer.
        
        Args:
            query: The original query
            result: The raw result from the contract call
            
        Returns:
            str: A human-readable formatted answer
        """
        try:
            function_meta = ERC20_FUNCTIONS[query.function]
            
            # Format based on return type
            if function_meta.return_type == "uint256":
                if function_meta.decimals_adjustment:
                    return f"{result:,.2f}"
                return f"{result:,}"
            elif function_meta.return_type == "string":
                return str(result)
            elif function_meta.return_type == "uint8":
                return str(result)
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error formatting answer: {str(e)}")
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