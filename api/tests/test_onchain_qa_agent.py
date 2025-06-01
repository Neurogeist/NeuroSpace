"""
Tests for the OnChainQAAgent class.
"""
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import re
from web3 import Web3
from web3.exceptions import ContractLogicError
import pytest
from datetime import datetime

from app.agents.onchain_qa import OnChainQAAgent
from app.agents.schemas import OnChainQuery, ERC20_FUNCTIONS, TOKEN_REGISTRY
from app.services.ipfs import IPFSService

class TestOnChainQAAgent(unittest.TestCase):
    """Test cases for OnChainQAAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = OnChainQAAgent(
            agent_id="test_agent",
            web3_provider="http://localhost:8545"
        )
        
        # Mock Web3 connection
        self.agent.web3.is_connected = MagicMock(return_value=True)
        
        # Mock contract functions
        self.mock_contract = MagicMock()
        self.agent._get_contract = MagicMock(return_value=self.mock_contract)
        
        # Mock IPFS service
        self.agent.ipfs_service = MagicMock(spec=IPFSService)
        self.agent.ipfs_service.upload_json = AsyncMock(return_value="test_ipfs_hash")
    
    def test_parse_question_known_query(self):
        """Test parsing a known query."""
        # Run the async code
        asyncio.run(self._test_parse_question_known_query())
    
    async def _test_parse_question_known_query(self):
        """Async implementation of known query parsing test."""
        question = "What is the total supply of neurocoin"
        query = await self.agent._parse_question(question)
        
        self.assertIsInstance(query, OnChainQuery)
        self.assertEqual(query.function, "totalSupply")
        self.assertEqual(query.abi_type, "ERC20")
        self.assertEqual(len(query.args), 0)
        self.assertEqual(query.contract_address, TOKEN_REGISTRY["neurocoin"])
    
    @patch.object(OnChainQAAgent, 'client')
    def test_parse_question_llm_fallback(self, mock_client):
        """Test LLM fallback for unknown queries."""
        # Run the async code
        asyncio.run(self._test_parse_question_llm_fallback(mock_client))
    
    async def _test_parse_question_llm_fallback(self, mock_client):
        """Async implementation of LLM fallback test."""
        # Mock LLM response
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "contract_address": TOKEN_REGISTRY["usdc"],
                "function": "balanceOf",
                "args": ["0x1234567890123456789012345678901234567890"],
                "abi_type": "ERC20"
            })))
        ]
        
        question = "What is the USDC balance of 0x1234567890123456789012345678901234567890"
        query = await self.agent._parse_question(question)
        
        self.assertIsInstance(query, OnChainQuery)
        self.assertEqual(query.function, "balanceOf")
        self.assertEqual(query.abi_type, "ERC20")
        self.assertEqual(len(query.args), 1)
        self.assertEqual(query.contract_address, TOKEN_REGISTRY["usdc"])
    
    def test_execute_query_success(self):
        """Test successful query execution."""
        # Run the async code
        asyncio.run(self._test_execute_query_success())
    
    async def _test_execute_query_success(self):
        """Async implementation of successful query test."""
        # Mock contract function
        mock_function = MagicMock()
        mock_function.call.return_value = 1000000
        self.mock_contract.functions.totalSupply = MagicMock(return_value=mock_function)
        self.mock_contract.functions.decimals = MagicMock(return_value=MagicMock(call=MagicMock(return_value=6)))
        
        query = OnChainQuery(
            contract_address=TOKEN_REGISTRY["usdc"],
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        
        result = await self.agent._execute_query(query)
        self.assertEqual(result, 1.0)  # 1000000 / 10^6
    
    def test_execute_query_revert(self):
        """Test query execution with revert."""
        # Run the async code
        asyncio.run(self._test_execute_query_revert())
    
    async def _test_execute_query_revert(self):
        """Async implementation of revert test."""
        # Mock contract function to raise ContractLogicError
        mock_function = MagicMock()
        mock_function.call.side_effect = ContractLogicError("execution reverted")
        self.mock_contract.functions.balanceOf = MagicMock(return_value=mock_function)
        
        query = OnChainQuery(
            contract_address=TOKEN_REGISTRY["usdc"],
            function="balanceOf",
            args=["0x1234567890123456789012345678901234567890"],
            abi_type="ERC20"
        )
        
        with self.assertRaises(ValueError) as context:
            await self.agent._execute_query(query)
        self.assertIn("reverted", str(context.exception))
    
    def test_format_answer(self):
        """Test answer formatting."""
        # Run the async code
        asyncio.run(self._test_format_answer())
    
    async def _test_format_answer(self):
        """Async implementation of answer formatting test."""
        query = OnChainQuery(
            contract_address=TOKEN_REGISTRY["usdc"],
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        
        # Test uint256 with decimals
        result = await self.agent._format_answer(query, 1000000)
        self.assertEqual(result, "1,000,000.00")
        
        # Test string
        query.function = "symbol"
        result = await self.agent._format_answer(query, "USDC")
        self.assertEqual(result, "USDC")
        
        # Test uint8
        query.function = "decimals"
        result = await self.agent._format_answer(query, 6)
        self.assertEqual(result, "6")
    
    def test_store_trace(self):
        """Test trace storage."""
        # Run the async code
        asyncio.run(self._test_store_trace())
    
    async def _test_store_trace(self):
        """Async implementation of trace storage test."""
        # Create a test trace
        self.agent.current_trace = ExecutionTrace(agent_id="test_agent")
        await self.agent.log_step(
            action="test_action",
            inputs={"test": "input"},
            outputs={"test": "output"}
        )
        await self.agent.finalize_trace()
        
        # Store trace
        ipfs_hash = await self.agent.store_trace()
        
        self.assertEqual(ipfs_hash, "test_ipfs_hash")
        self.agent.ipfs_service.upload_json.assert_called_once()
    
    def test_retry_logic(self):
        """Test retry logic for failed operations."""
        # Run the async code
        asyncio.run(self._test_retry_logic())
    
    async def _test_retry_logic(self):
        """Async implementation of retry logic test."""
        # Mock contract function to fail twice then succeed
        mock_function = MagicMock()
        mock_function.call.side_effect = [
            ContractLogicError("temporary error"),
            ContractLogicError("temporary error"),
            1000000
        ]
        self.mock_contract.functions.totalSupply = MagicMock(return_value=mock_function)
        self.mock_contract.functions.decimals = MagicMock(return_value=MagicMock(call=MagicMock(return_value=6)))
        
        query = OnChainQuery(
            contract_address=TOKEN_REGISTRY["usdc"],
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        
        result = await self.agent._execute_query(query)
        self.assertEqual(result, 1.0)
        self.assertEqual(mock_function.call.call_count, 3)
    
    def test_cache_behavior(self):
        """Test caching behavior."""
        # Run the async code
        asyncio.run(self._test_cache_behavior())
    
    async def _test_cache_behavior(self):
        """Async implementation of cache behavior test."""
        # Mock contract function
        mock_function = MagicMock()
        mock_function.call.return_value = 1000000
        self.mock_contract.functions.totalSupply = MagicMock(return_value=mock_function)
        self.mock_contract.functions.decimals = MagicMock(return_value=MagicMock(call=MagicMock(return_value=6)))
        
        query = OnChainQuery(
            contract_address=TOKEN_REGISTRY["usdc"],
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        
        # First call should use cache
        result1 = await self.agent._execute_query(query)
        self.assertEqual(result1, 1.0)
        
        # Second call should use cached contract
        result2 = await self.agent._execute_query(query)
        self.assertEqual(result2, 1.0)
        
        # Verify contract was only created once
        self.agent._get_contract.assert_called_once_with(query.contract_address)

if __name__ == '__main__':
    unittest.main() 