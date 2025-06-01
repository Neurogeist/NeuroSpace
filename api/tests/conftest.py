import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, Mock

pytest_plugins = ["pytest_asyncio"]

# Completely fake out the transformers module
sys.modules["transformers"] = MagicMock()

from api.app.main import app
from api.app.models.database import Base, get_db
from api.app.services.blockchain import BlockchainService
from api.app.services.ipfs import IPFSService
from api.app.services.llm import LLMService
from api.app.services.chat_session import ChatSessionService
from api.app.services.model_registry import ModelRegistry
from api.app.services.payment import PaymentService
from api.app.services.rag import RAGService
from api.app.services.flagging import FlaggingService

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    logger.debug("Setting up test database")
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def mock_blockchain_service():
    """Mock blockchain service for testing."""
    logger.debug("Setting up mock blockchain service")
    mock = Mock(spec=BlockchainService)
    
    # Mock web3 and its required attributes
    mock_web3 = Mock()
    mock_web3.is_connected = Mock(return_value=True)
    mock_web3.eth = Mock()
    mock_web3.eth.chain_id = 1
    mock.web3 = mock_web3
    
    # Mock account
    mock_account = Mock()
    mock_account.address = "0x1234567890123456789012345678901234567890"
    mock.account = mock_account
    
    # Mock other required methods
    mock.verify_signature = AsyncMock(return_value={
        "is_valid": True,
        "recovered_address": mock_account.address,
        "matches_expected": True
    })
    mock.sign_message = AsyncMock(return_value="0x" + "1" * 130)
    
    return mock

@pytest.fixture(scope="function")
def mock_model_registry():
    """Mock model registry for testing."""
    logger.debug("Setting up mock model registry")
    mock = Mock(spec=ModelRegistry)
    mock.get_available_models = Mock(return_value={
        "mixtral-8x7b-instruct": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "gemma-2-27b-it": "google/gemma-2-27b-it"
    })
    return mock

@pytest.fixture(scope="function")
def mock_llm_service(mock_model_registry):
    """Mock LLM service for testing."""
    logger.debug("Setting up mock LLM service")
    mock = Mock(spec=LLMService)
    mock.model = Mock()
    mock.tokenizer = Mock()
    mock.model_registry = mock_model_registry
    mock.get_available_models = Mock(return_value={
        "mixtral-8x7b-instruct": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "gemma-2-27b-it": "google/gemma-2-27b-it"
    })
    return mock

@pytest.fixture(scope="function")
def mock_ipfs_service():
    """Mock IPFS service for testing."""
    logger.debug("Setting up mock IPFS service")
    mock = Mock(spec=IPFSService)
    mock.client = Mock()
    mock.upload_file = AsyncMock(return_value="QmTestHash")
    mock.get_file = AsyncMock(return_value=b"test content")
    return mock

@pytest.fixture(scope="function")
def mock_payment_service():
    """Mock payment service for testing."""
    logger.debug("Setting up mock payment service")
    mock = Mock(spec=PaymentService)
    mock.verify_payment = AsyncMock(return_value=True)
    mock.get_free_requests = AsyncMock(return_value=5)
    return mock

@pytest.fixture(scope="function")
def mock_rag_service():
    """Mock RAG service for testing."""
    logger.debug("Setting up mock RAG service")
    mock = Mock(spec=RAGService)
    mock.query_documents = AsyncMock(return_value={
        "response": "Test RAG response",
        "sources": ["source1", "source2"]
    })
    return mock

@pytest.fixture(scope="function")
def mock_chat_session_service():
    """Mock chat session service for testing."""
    logger.debug("Setting up mock chat session service")
    mock = Mock(spec=ChatSessionService)
    mock.create_session = AsyncMock(return_value="test-session-id")
    mock.get_session = AsyncMock(return_value="test-session-id")
    mock.get_all_sessions = AsyncMock(return_value=["test-session-id"])
    mock.get_session_history = AsyncMock(return_value=["test-message"])
    mock.get_session_summary = AsyncMock(return_value="test-summary")
    mock.get_session_status = AsyncMock(return_value="completed")
    mock.update_session_status = AsyncMock(return_value=True)
    mock.update_session_history = AsyncMock(return_value=True)
    mock.update_session_summary = AsyncMock(return_value=True)
    mock.delete_session = AsyncMock(return_value=True)
    return mock

@pytest.fixture(scope="function")
def mock_flagging_service():
    """Mock flagging service for testing."""
    logger.debug("Setting up mock flagging service")
    mock = Mock(spec=FlaggingService)
    mock.flag_content = AsyncMock(return_value=True)
    mock.unflag_content = AsyncMock(return_value=True)
    mock.get_flagged_contents = AsyncMock(return_value=["test-content"])
    mock.get_flagged_contents_count = AsyncMock(return_value=1)
    return mock

@pytest.fixture(scope="function")
def client(
    mock_blockchain_service,
    mock_ipfs_service,
    mock_llm_service,
    mock_model_registry,
    mock_payment_service,
    mock_rag_service,
    mock_chat_session_service,
    mock_flagging_service,
    db_session
):
    """Create a test client with mocked services."""
    logger.debug("Setting up test client")
    
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Reset app state
    app.dependency_overrides = {}
    
    # Override services
    app.blockchain_service = mock_blockchain_service
    app.ipfs_service = mock_ipfs_service
    app.llm_service = mock_llm_service
    app.model_registry = mock_model_registry
    app.payment_service = mock_payment_service
    app.rag_service = mock_rag_service
    app.chat_session_service = mock_chat_session_service
    app.flagging_service = mock_flagging_service
    
    # Ensure blockchain service is properly initialized
    if not hasattr(app.blockchain_service, 'web3'):
        mock_web3 = Mock()
        mock_web3.is_connected = Mock(return_value=True)
        mock_web3.eth = Mock()
        mock_web3.eth.chain_id = 1
        app.blockchain_service.web3 = mock_web3
    
    # Override database dependency
    app.dependency_overrides["get_db"] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides = {}

@pytest.fixture
def test_wallet_address():
    """Test wallet address for testing."""
    return "0x1234567890123456789012345678901234567890"

@pytest.fixture
def test_session_id():
    """Test session ID for testing."""
    return str(uuid.uuid4())

@pytest.fixture
def test_file():
    """Test file for upload testing."""
    return {
        "file": ("test.txt", b"test content", "text/plain"),
        "wallet_address": "0x1234567890123456789012345678901234567890"
    }

@pytest.fixture
def test_prompt_data(test_wallet_address, test_session_id):
    """Test prompt data for testing."""
    return {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "user_address": test_wallet_address,
        "session_id": test_session_id,
        "payment_method": "ETH"
    }

@pytest.fixture
def test_verification_data(test_wallet_address):
    """Test verification data for testing."""
    return {
        "verification_hash": "0x" + "1" * 64,
        "signature": "0x" + "1" * 130,
        "expected_address": test_wallet_address
    } 