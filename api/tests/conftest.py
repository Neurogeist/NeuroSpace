import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.app.main import app

# Test client
@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

# Mock file upload
@pytest.fixture
def mock_file():
    return {
        'file': ('test.pdf', b'fake pdf content', 'application/pdf')
    }

# Mock wallet
@pytest.fixture
def mock_wallet():
    return {
        'address': '0x1234567890123456789012345678901234567890',
        'private_key': '0x' + '1' * 64
    }

# Mock Redis
@pytest.fixture
def mock_redis():
    with patch('redis.Redis') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

# Mock IP address
@pytest.fixture
def mock_ip():
    return '192.168.1.1'

# Mock services
@pytest.fixture(autouse=True)
def mock_services():
    """Mock all external services used by the app"""
    with patch('api.app.services.blockchain.BlockchainService') as mock_blockchain, \
         patch('api.app.services.llm.LLMService') as mock_llm, \
         patch('api.app.services.ipfs.IPFSService') as mock_ipfs, \
         patch('api.app.services.chat_session.ChatSessionService') as mock_chat, \
         patch('api.app.services.model_registry.ModelRegistry') as mock_model_registry, \
         patch('api.app.services.payment.PaymentService') as mock_payment, \
         patch('api.app.services.rag.RAGService') as mock_rag, \
         patch('api.app.services.flagging.FlaggingService') as mock_flagging:
        
        # Configure mock blockchain service
        blockchain_instance = Mock()
        blockchain_instance.web3 = Mock()
        blockchain_instance.contract = Mock()
        blockchain_instance.is_connected.return_value = True
        mock_blockchain.return_value = blockchain_instance
        
        # Configure mock IPFS service
        ipfs_instance = Mock()
        ipfs_instance.add.return_value = {'Hash': 'test_hash'}
        mock_ipfs.return_value = ipfs_instance
        
        # Configure other service mocks
        mock_llm.return_value = Mock()
        mock_chat.return_value = Mock()
        mock_model_registry.return_value = Mock()
        mock_payment.return_value = Mock()
        mock_rag.return_value = Mock()
        mock_flagging.return_value = Mock()
        
        yield {
            'blockchain': mock_blockchain,
            'llm': mock_llm,
            'ipfs': mock_ipfs,
            'chat': mock_chat,
            'model_registry': mock_model_registry,
            'payment': mock_payment,
            'rag': mock_rag,
            'flagging': mock_flagging
        } 