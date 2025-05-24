"""
Tests for the OnChainQAAgent class.
"""
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import re

from api.app.agents.onchain_qa import OnChainQAAgent
from api.app.services.ipfs import IPFSService

class TestOnChainQAAgent(unittest.TestCase):
    """Test cases for OnChainQAAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = OnChainQAAgent(
            agent_id="test_agent",
            web3_provider="http://localhost:8545"
        )
    
    def test_logging_and_finalizing_trace(self):
        """Test logging a step and finalizing the trace."""
        # Run the async code
        asyncio.run(self._test_logging_and_finalizing_trace())
    
    async def _test_logging_and_finalizing_trace(self):
        """Async implementation of logging and finalizing test."""
        # Log a step
        step = await self.agent.log_step(
            action="parse_question",
            inputs={"question": "What is the total supply?"},
            outputs={"parsed_query": {"function": "totalSupply"}},
            metadata={}
        )
        
        # Finalize the trace
        commitment_hash = await self.agent.finalize_trace()
        
        # Assertions
        self.assertIsNotNone(self.agent.current_trace)
        self.assertEqual(len(self.agent.current_trace.steps), 1)
        self.assertEqual(self.agent.current_trace.steps[0], step)
        self.assertIsNotNone(commitment_hash)
        self.assertEqual(self.agent.current_trace.commitment_hash, commitment_hash)
        
        # Verify step content
        self.assertEqual(step.action, "parse_question")
        self.assertEqual(step.inputs["question"], "What is the total supply?")
        self.assertEqual(step.outputs["parsed_query"]["function"], "totalSupply")
    
    @patch.object(IPFSService, 'upload_json')
    def test_ipfs_upload(self, mock_upload_json):
        """Test storing trace on IPFS with mocked service."""
        # Run the async code
        asyncio.run(self._test_ipfs_upload(mock_upload_json))
    
    async def _test_ipfs_upload(self, mock_upload_json):
        """Async implementation of IPFS upload test."""
        # Mock the IPFS upload
        mock_ipfs_hash = "QmTestHash123"
        mock_upload_json.return_value = mock_ipfs_hash
        
        # Log a step and finalize
        await self.agent.log_step(
            action="test_step",
            inputs={"test": "input"},
            outputs={"test": "output"},
            metadata={}
        )
        await self.agent.finalize_trace()
        
        # Store trace
        ipfs_hash = await self.agent.store_trace()
        
        # Assertions
        self.assertEqual(ipfs_hash, mock_ipfs_hash)
        self.assertEqual(self.agent.current_trace.ipfs_hash, mock_ipfs_hash)
        mock_upload_json.assert_called_once()
        
        # Verify the uploaded data
        call_args = mock_upload_json.call_args[0][0]
        self.assertIn("trace_id", call_args)
        self.assertIn("steps", call_args)
        self.assertEqual(len(call_args["steps"]), 1)
    
    @patch.object(OnChainQAAgent, '_execute_query')
    @patch.object(OnChainQAAgent, '_format_answer')
    @patch.object(IPFSService, 'upload_json')
    def test_full_execute_run(self, mock_upload_json, mock_format_answer, mock_execute_query):
        """Test the full execute() method with mocked dependencies."""
        # Run the async code
        asyncio.run(self._test_full_execute_run(mock_upload_json, mock_format_answer, mock_execute_query))
    
    async def _test_full_execute_run(self, mock_upload_json, mock_format_answer, mock_execute_query):
        """Async implementation of full execute test."""
        # Mock the dependencies
        mock_execute_query.return_value = {"totalSupply": "1000000"}
        mock_format_answer.return_value = "The total supply is 1,000,000 tokens"
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
        self.assertEqual(result["answer"], "The total supply is 1,000,000 tokens")
        
        # Verify the hashes
        self.assertEqual(result["ipfs_hash"], mock_ipfs_hash)
        self.assertIsNotNone(result["commitment_hash"])
        self.assertTrue(re.match(r"^0x[a-f0-9]{40}$", result["transaction_hash"]))
        
        # Verify the trace metadata
        self.assertIsInstance(result["trace_metadata"], dict)
        self.assertEqual(result["trace_metadata"]["ipfs_hash"], mock_ipfs_hash)
        self.assertEqual(len(result["trace_metadata"]["steps"]), 3)  # parse, execute, format
        
        # Verify the mocks were called
        mock_execute_query.assert_called_once()
        mock_format_answer.assert_called_once()
        mock_upload_json.assert_called_once()

if __name__ == '__main__':
    unittest.main() 