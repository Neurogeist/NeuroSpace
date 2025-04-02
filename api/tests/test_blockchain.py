import pytest
from unittest.mock import Mock, patch
from api.app.services.blockchain import BlockchainService
from api.tests.test_config import TestSettings

@pytest.fixture
def blockchain_service():
    with patch('api.app.services.blockchain.get_settings', return_value=TestSettings()):
        service = BlockchainService()
        return service

def test_blockchain_initialization(blockchain_service):
    """Test that blockchain service initializes correctly."""
    assert blockchain_service.w3.is_connected()
    assert blockchain_service.account.address is not None

def test_hash_prompt(blockchain_service):
    """Test prompt hashing."""
    prompt = "What is the capital of France?"
    response = "Paris"
    timestamp = "2024-02-20T12:00:00"
    user_address = "0x123...abc"
    
    hash_result = blockchain_service.hash_prompt(prompt, response, timestamp, user_address)
    assert len(hash_result) == 64  # SHA-256 hash length
    assert hash_result.isalnum()

@pytest.mark.asyncio
async def test_submit_hash(blockchain_service):
    """Test hash submission to blockchain."""
    with patch('api.app.services.blockchain.Web3') as mock_web3:
        # Mock the transaction receipt
        mock_receipt = Mock()
        mock_receipt.transactionHash = Mock()
        mock_receipt.transactionHash.hex.return_value = "0x123..."
        
        # Mock the transaction sending
        mock_web3.eth.send_raw_transaction.return_value = "0x123..."
        mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt
        
        # Mock gas price
        mock_web3.eth.gas_price = 1000000000
        
        # Mock nonce
        mock_web3.eth.get_transaction_count.return_value = 0
        
        # Test hash submission with a valid hex string
        test_hash = "0x" + "1" * 64
        hash_result = blockchain_service.submit_hash(test_hash)
        assert hash_result == "0x123..." 