import pytest
from unittest.mock import Mock, patch
from api.app.services.llm import LLMService
from api.app.services.blockchain import BlockchainService
from api.app.services.ipfs import IPFSService
from api.tests.test_config import TestSettings

@pytest.fixture
def test_settings():
    return TestSettings()

@pytest.fixture
def llm_service(test_settings):
    with patch('api.app.services.llm.get_settings', return_value=test_settings):
        service = LLMService()
        return service

@pytest.fixture
def blockchain_service(test_settings):
    with patch('api.app.services.blockchain.get_settings', return_value=test_settings):
        service = BlockchainService()
        return service

@pytest.fixture
def ipfs_service(test_settings):
    with patch('api.app.services.ipfs.get_settings', return_value=test_settings):
        service = IPFSService()
        return service

@pytest.fixture
def mock_llm_response():
    return "Paris is the capital of France."

@pytest.fixture
def mock_ipfs_response():
    return {
        "IpfsHash": "QmTest123...",
        "PinSize": 100,
        "Timestamp": "2024-02-20T12:00:00"
    }

@pytest.fixture
def mock_blockchain_response():
    return "0x123..."

@pytest.fixture
def sample_prompt_data():
    return {
        "prompt": "What is the capital of France?",
        "user_address": "0x123...abc"
    } 