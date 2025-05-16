import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch, AsyncMock
import os
from datetime import datetime, timedelta
import uuid
import logging
import asyncio

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
    with patch('api.app.main.blockchain_service') as mock:
        mock.web3 = Mock()
        mock.sign_message = AsyncMock(return_value="0x" + "1" * 130)
        mock.verify_signature = AsyncMock(return_value=True)
        mock.verify_hash = AsyncMock(return_value=True)
        mock.get_signer_address = AsyncMock(return_value="0x1234567890123456789012345678901234567890")
        yield mock

@pytest.fixture(scope="function")
def mock_ipfs_service():
    """Mock IPFS service for testing."""
    logger.debug("Setting up mock IPFS service")
    with patch('api.app.main.ipfs_service') as mock:
        mock.client = Mock()
        mock.upload_file = AsyncMock(return_value="QmTestHash")
        mock.get_file = AsyncMock(return_value=b"test content")
        yield mock

@pytest.fixture(scope="function")
def mock_llm_service():
    """Mock LLM service for testing."""
    logger.debug("Setting up mock LLM service")
    with patch('api.app.main.llm_service') as mock:
        mock.model = Mock()
        mock.tokenizer = Mock()
        mock.generate_response = AsyncMock(return_value={
            "response": "Test response",
            "model_name": "test-model",
            "model_id": "test-model-id"
        })
        yield mock

@pytest.fixture(scope="function")
def mock_model_registry():
    """Mock model registry for testing."""
    logger.debug("Setting up mock model registry")
    with patch('api.app.main.model_registry') as mock:
        mock.get_available_models = AsyncMock(return_value={
            "mixtral-8x7b-instruct": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "gemma-2-27b-it": "google/gemma-2-27b-it"
        })
        yield mock

@pytest.fixture(scope="function")
def mock_payment_service():
    """Mock payment service for testing."""
    logger.debug("Setting up mock payment service")
    with patch('api.app.main.payment_service') as mock:
        mock.verify_payment = AsyncMock(return_value=True)
        mock.get_free_requests = AsyncMock(return_value=5)
        yield mock

@pytest.fixture(scope="function")
def mock_rag_service():
    """Mock RAG service for testing."""
    logger.debug("Setting up mock RAG service")
    with patch('api.app.main.rag_service') as mock:
        mock.query_documents = AsyncMock(return_value={
            "response": "Test RAG response",
            "sources": ["source1", "source2"]
        })
        yield mock

@pytest.fixture(scope="function")
def client(db_session, mock_blockchain_service, mock_ipfs_service, 
           mock_llm_service, mock_model_registry, mock_payment_service, 
           mock_rag_service):
    """Create a test client with mocked services."""
    logger.debug("Setting up test client")
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

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