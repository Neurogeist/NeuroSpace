"""
Tests for the OnChainQAAgent class.
"""
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import re
from web3 import Web3

from app.agents.onchain_qa import OnChainQAAgent
from app.agents.schemas import OnChainQuery, ERC20_FUNCTIONS
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
    
    @patch.object(OnChainQAAgent, 'client')
    def test_parse_question_llm_fallback(self, mock_client):
        """Test LLM fallback for unknown queries."""
        # Run the async code
        asyncio.run(self._test_parse_question_llm_fallback(mock_client))
    
    async def _test_parse_question_llm_fallback(self, mock_client):
        """Async implementation of LLM fallback test."""
        # Mock LLM response
        mock_response = {
            "contract_address": "0x1234567890123456789012345678901234567890",
            "function": "balanceOf",
            "args": ["0x0987654321098765432109876543210987654321"],
            "abi_type": "ERC20"
        }
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_response)))
        ]
        
        question = "What is the balance of 0x0987654321098765432109876543210987654321"
        query = await self.agent._parse_question(question)
        
        self.assertIsInstance(query, OnChainQuery)
        self.assertEqual(query.function, "balanceOf")
        self.assertEqual(len(query.args), 1)
        self.assertEqual(query.args[0], "0x0987654321098765432109876543210987654321")
    
    @patch.object(Web3.eth.Contract, 'functions')
    def test_execute_query(self, mock_contract_functions):
        """Test executing a query."""
        # Run the async code
        asyncio.run(self._test_execute_query(mock_contract_functions))
    
    async def _test_execute_query(self, mock_contract_functions):
        """Async implementation of query execution test."""
        # Mock contract function calls
        mock_total_supply = MagicMock()
        mock_total_supply.call.return_value = 1000000
        mock_decimals = MagicMock()
        mock_decimals.call.return_value = 18
        mock_contract_functions.totalSupply.return_value = mock_total_supply
        mock_contract_functions.decimals.return_value = mock_decimals
        
        query = OnChainQuery(
            contract_address="0x1234567890123456789012345678901234567890",
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        
        result = await self.agent._execute_query(query)
        
        self.assertEqual(result, 1.0)  # 1000000 / 10^18
        mock_total_supply.call.assert_called_once()
        mock_decimals.call.assert_called_once()
    
    def test_format_answer(self):
        """Test formatting different types of answers."""
        # Run the async code
        asyncio.run(self._test_format_answer())
    
    async def _test_format_answer(self):
        """Async implementation of answer formatting test."""
        # Test uint256 with decimals
        query = OnChainQuery(
            contract_address="0x1234567890123456789012345678901234567890",
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        result = 1234567.89
        formatted = await self.agent._format_answer(query, result)
        self.assertEqual(formatted, "1,234,567.89")
        
        # Test string
        query.function = "symbol"
        result = "USDC"
        formatted = await self.agent._format_answer(query, result)
        self.assertEqual(formatted, "USDC")
        
        # Test uint8
        query.function = "decimals"
        result = 18
        formatted = await self.agent._format_answer(query, result)
        self.assertEqual(formatted, "18")
    
    @patch.object(OnChainQAAgent, '_parse_question')
    @patch.object(OnChainQAAgent, '_execute_query')
    @patch.object(OnChainQAAgent, '_format_answer')
    @patch.object(IPFSService, 'upload_json')
    def test_full_execute_run(self, mock_upload_json, mock_format_answer, 
                            mock_execute_query, mock_parse_question):
        """Test the full execute() method with mocked dependencies."""
        # Run the async code
        asyncio.run(self._test_full_execute_run(mock_upload_json, mock_format_answer, 
                                              mock_execute_query, mock_parse_question))
    
    async def _test_full_execute_run(self, mock_upload_json, mock_format_answer, 
                                   mock_execute_query, mock_parse_question):
        """Async implementation of full execute test."""
        # Mock the dependencies
        mock_query = OnChainQuery(
            contract_address="0x1234567890123456789012345678901234567890",
            function="totalSupply",
            args=[],
            abi_type="ERC20"
        )
        mock_parse_question.return_value = mock_query
        mock_execute_query.return_value = 1000000
        mock_format_answer.return_value = "1,000,000"
        mock_ipfs_hash = "QmTestHash456"
        mock_upload_json.return_value = mock_ipfs_hash
        
        # Execute the agent
        result = await self.agent.execute("What is the total supply?")
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("trace_id", result)
        self.assertIn("ipfs_hash", result)
        self.assertIn("commitment_hash", result)
        self.assertIn("trace_metadata", result)
        
        # Verify the answer
        self.assertEqual(result["answer"], "1,000,000")
        
        # Verify the hashes
        self.assertEqual(result["ipfs_hash"], mock_ipfs_hash)
        self.assertIsNotNone(result["commitment_hash"])
        
        # Verify the trace metadata
        self.assertIsInstance(result["trace_metadata"], dict)
        self.assertEqual(result["trace_metadata"]["ipfs_hash"], mock_ipfs_hash)
        self.assertEqual(len(result["trace_metadata"]["steps"]), 3)  # parse, execute, format
        
        # Verify the mocks were called
        mock_parse_question.assert_called_once()
        mock_execute_query.assert_called_once()
        mock_format_answer.assert_called_once()
        mock_upload_json.assert_called_once()

if __name__ == '__main__':
    unittest.main() 