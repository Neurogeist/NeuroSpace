"""
On-Chain Question Answering Agent

This agent handles natural language questions about on-chain data,
performs the necessary queries, and maintains a verifiable execution trace.
"""
import logging
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, List
import os
import openai
from openai import OpenAI
from web3 import Web3
from web3.exceptions import ContractLogicError
from web3.middleware import geth_poa_middleware

from .base import BaseAgent, ExecutionStep, ExecutionTrace
from .schemas import OnChainQuery, ERC20_FUNCTIONS, SYSTEM_PROMPT, TOKEN_REGISTRY
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

# Regular expression for Ethereum addresses
ETH_ADDRESS_PATTERN = re.compile(r'0x[a-fA-F0-9]{40}')

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
    
    def _extract_addresses(self, text: str) -> List[str]:
        """
        Extract Ethereum addresses from text.
        
        Args:
            text: Text to search for addresses
            
        Returns:
            List[str]: List of found addresses
        """
        return ETH_ADDRESS_PATTERN.findall(text)
    
    def _extract_token_names(self, text: str) -> List[str]:
        """
        Extract potential token names from text.
        
        Args:
            text: Text to search for token names
            
        Returns:
            List[str]: List of found token names
        """
        # Convert text to lowercase and split into words
        words = text.lower().strip().split()
        
        # Log the words we're checking
        logger.debug(f"Checking words for token names: {words}")
        
        # Check each word against the token registry
        found_tokens = []
        for word in words:
            # Remove any punctuation
            clean_word = word.strip('.,!?')
            if clean_word in TOKEN_REGISTRY:
                found_tokens.append(clean_word)
                logger.info(f"Found token name: {clean_word}")
        
        # If no exact matches, try partial matches
        if not found_tokens:
            for word in words:
                clean_word = word.strip('.,!?')
                # Check if any token name contains this word
                for token_name in TOKEN_REGISTRY.keys():
                    if clean_word in token_name or token_name in clean_word:
                        found_tokens.append(token_name)
                        logger.info(f"Found partial token match: {clean_word} -> {token_name}")
        
        logger.info(f"Extracted token names: {found_tokens}")
        return found_tokens
    
    def _validate_query(self, query: OnChainQuery) -> Tuple[bool, Optional[str]]:
        """
        Validate a query and return helpful error messages.
        
        Args:
            query: The query to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check if function exists
        if query.function not in ERC20_FUNCTIONS:
            return False, f"Unsupported function: {query.function}"
        
        # Get function metadata
        function_meta = ERC20_FUNCTIONS[query.function]
        
        # Check argument count
        if len(query.args) != len(function_meta.args):
            required_args = [arg.name for arg in function_meta.args]
            return False, (
                f"Function {query.function} requires {len(function_meta.args)} arguments: "
                f"{', '.join(required_args)}"
            )
        
        # Check argument types
        for i, (arg, meta) in enumerate(zip(query.args, function_meta.args)):
            if meta.type == "address" and not Web3.is_address(arg):
                return False, f"Argument {i+1} ({meta.name}) must be a valid Ethereum address"
        
        return True, None
    
    async def execute(self, question: str) -> Dict[str, Any]:
        """
        Execute the question answering process.
        
        Args:
            question: Natural language question about on-chain data
            
        Returns:
            Dict containing the answer and execution trace information
        """
        try:
            # Initialize new trace
            self.current_trace = ExecutionTrace(agent_id=self.agent_id)
            logger.info(f"Starting new execution trace: {self.current_trace.trace_id}")
            
            # Parse the question
            parsed_query = await self._parse_question(question)
            await self.log_step(
                action="parse_question",
                inputs={"question": question},
                outputs={"parsed_query": parsed_query.dict()},
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            
            # Execute the query
            result = await self._execute_query(parsed_query)
            await self.log_step(
                action="execute_query",
                inputs={"parsed_query": parsed_query.dict()},
                outputs={"result": result},
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "contract_address": parsed_query.contract_address,
                    "function": parsed_query.function
                }
            )
            
            # Format the answer
            answer = await self._format_answer(parsed_query, result)
            await self.log_step(
                action="format_answer",
                inputs={"result": result},
                outputs={"answer": answer},
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            
            # Finalize trace and compute commitment hash
            logger.info("Finalizing trace and computing commitment hash...")
            commitment_hash = await self.finalize_trace()
            logger.info(f"Computed commitment hash: {commitment_hash}")
            
            # Store trace on IPFS
            logger.info("Storing trace on IPFS...")
            ipfs_hash = await self.store_trace()
            logger.info(f"Stored trace on IPFS with hash: {ipfs_hash}")
            
            # Verify trace is complete
            if not self.current_trace.commitment_hash or not self.current_trace.ipfs_hash:
                raise ValueError("Trace is incomplete - missing commitment or IPFS hash")
            
            # Prepare response with full trace metadata
            response = {
                "answer": answer,
                "trace_id": self.current_trace.trace_id,
                "ipfs_hash": ipfs_hash,
                "commitment_hash": commitment_hash,
                "trace_metadata": {
                    "agent_id": self.current_trace.agent_id,
                    "start_time": self.current_trace.start_time.isoformat() if self.current_trace.start_time else None,
                    "end_time": self.current_trace.end_time.isoformat() if self.current_trace.end_time else None,
                    "steps": [
                        {
                            "step_id": step.step_id,
                            "action": step.action,
                            "timestamp": step.timestamp.isoformat() if step.timestamp else None,
                            "inputs": step.inputs,
                            "outputs": step.outputs,
                            "metadata": step.metadata,
                            "step_hash": step.compute_hash()
                        }
                        for step in self.current_trace.steps
                    ],
                    "commitment_hash": self.current_trace.commitment_hash,
                    "ipfs_hash": self.current_trace.ipfs_hash
                }
            }
            
            logger.info(f"Execution complete. Trace ID: {self.current_trace.trace_id}")
            return response
            
        except Exception as e:
            # Log the error
            await self.log_step(
                action="error",
                inputs={"question": question},
                outputs={"error": str(e)},
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": type(e).__name__
                }
            )
            # Finalize trace even on error to maintain verifiability
            try:
                await self.finalize_trace()
                await self.store_trace()
            except Exception as trace_error:
                logger.error(f"Failed to finalize error trace: {str(trace_error)}")
            
            # Re-raise with user-friendly message
            if isinstance(e, ValueError):
                raise ValueError(str(e))
            raise ValueError(
                "I encountered an unexpected error. Please try rephrasing your question "
                "or contact support if the issue persists."
            )
    
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

            # Extract addresses and token names
            addresses = self._extract_addresses(question)
            token_names = self._extract_token_names(question)
            
            # If we found a token name, try to resolve it
            contract_address = None
            if token_names:
                for token_name in token_names:
                    contract_address = OnChainQuery.resolve_token_name(token_name)
                    if contract_address:
                        logger.info(f"Resolved token name '{token_name}' to address: {contract_address}")
                        break
            
            # If we found an address, use it
            if not contract_address and addresses:
                contract_address = addresses[0]
                logger.info(f"Using provided address: {contract_address}")
            
            # If no contract address found, raise error
            if not contract_address:
                raise ValueError(
                    "No valid contract address found. Please specify a known token name "
                    "(USDC, WETH, etc.) or provide a valid contract address."
                )
            
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
            content = completion.choices[0].message.content.strip()
            
            # Log the raw response for debugging
            logger.debug(f"Raw LLM response: {content}")
            
            # Try to extract JSON from the response
            try:
                # First try direct JSON parsing
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError(
                            "I had trouble understanding your question. Please try rephrasing it "
                            "or use one of these example formats:\n"
                            "1. 'What is the total supply of USDC?'\n"
                            "2. 'What is the balance of 0x123...?'\n"
                            "3. 'How many decimals does WETH have?'"
                        )
                else:
                    raise ValueError(
                        "I had trouble understanding your question. Please try rephrasing it "
                        "or use one of these example formats:\n"
                        "1. 'What is the total supply of USDC?'\n"
                        "2. 'What is the balance of 0x123...?'\n"
                        "3. 'How many decimals does WETH have?'"
                    )
            
            # Always use our resolved contract address
            parsed["contract_address"] = contract_address
            
            # Validate required fields
            required_fields = ["function", "args", "abi_type"]
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields in response: {', '.join(missing_fields)}. "
                    "Please try rephrasing your question."
                )
            
            query = OnChainQuery(**parsed)
            
            # Validate the query
            is_valid, error_msg = self._validate_query(query)
            if not is_valid:
                raise ValueError(error_msg)
            
            return query

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(
                "I had trouble understanding your question. Please try rephrasing it "
                "or use one of these example formats:\n"
                "1. 'What is the total supply of USDC?'\n"
                "2. 'What is the balance of 0x123...?'\n"
                "3. 'How many decimals does WETH have?'"
            )
        except Exception as e:
            logger.error(f"Failed to parse question: {e}")
            raise ValueError(
                "I couldn't understand your question. Please try:\n"
                "1. Using a known token name (USDC, WETH, etc.)\n"
                "2. Providing a valid contract address\n"
                "3. Using one of these functions: " + 
                ", ".join(ERC20_FUNCTIONS.keys())
            )
    
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
            # Ensure trace is finalized
            if not self.current_trace.commitment_hash:
                await self.finalize_trace()
            
            # Convert trace to serializable dictionary with all metadata
            trace_data = {
                "trace_id": self.current_trace.trace_id,
                "agent_id": self.current_trace.agent_id,
                "start_time": self.current_trace.start_time.isoformat() if self.current_trace.start_time else None,
                "end_time": self.current_trace.end_time.isoformat() if self.current_trace.end_time else None,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "action": step.action,
                        "timestamp": step.timestamp.isoformat() if step.timestamp else None,
                        "inputs": step.inputs,
                        "outputs": step.outputs,
                        "metadata": step.metadata,
                        "step_hash": step.compute_hash()
                    }
                    for step in self.current_trace.steps
                ],
                "commitment_hash": self.current_trace.commitment_hash,
                "ipfs_hash": self.current_trace.ipfs_hash
            }
            
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