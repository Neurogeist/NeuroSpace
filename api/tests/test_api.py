import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from api.app.main import app
from api.app.models.prompt import PromptRequest, PromptResponse

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_services():
    with patch("api.app.main.llm_service") as mock_llm, \
         patch("api.app.main.blockchain_service") as mock_blockchain, \
         patch("api.app.main.ipfs_service") as mock_ipfs:
        
        # Mock LLM service
        mock_llm.generate_response.return_value = "Test response"
        
        # Mock IPFS service
        mock_ipfs.upload_to_ipfs.return_value = {"IpfsHash": "test_cid"}
        
        # Mock blockchain service
        mock_blockchain.hash_prompt.return_value = "0x" + "1" * 64
        mock_blockchain.submit_hash.return_value = "0x" + "2" * 64
        
        yield {
            "llm": mock_llm,
            "blockchain": mock_blockchain,
            "ipfs": mock_ipfs
        }

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_submit_prompt_success(client, mock_services):
    request_data = {
        "prompt": "Test prompt",
        "user_address": "0x123",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/prompts", json=request_data)
    assert response.status_code == 200
    
    response_data = response.json()
    assert response_data["response"] == "Test response"
    assert response_data["ipfs_cid"] == "test_cid"
    assert response_data["signature"] == "0x" + "2" * 64

def test_submit_prompt_llm_error(client, mock_services):
    mock_services["llm"].generate_response.side_effect = Exception("LLM error")
    
    request_data = {
        "prompt": "Test prompt",
        "user_address": "0x123",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/prompts", json=request_data)
    assert response.status_code == 500
    assert "LLM error" in response.json()["detail"]

def test_submit_prompt_ipfs_error(client, mock_services):
    mock_services["ipfs"].upload_to_ipfs.side_effect = Exception("IPFS error")
    
    request_data = {
        "prompt": "Test prompt",
        "user_address": "0x123",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/prompts", json=request_data)
    assert response.status_code == 500
    assert "IPFS error" in response.json()["detail"]

def test_submit_prompt_blockchain_error(client, mock_services):
    mock_services["blockchain"].submit_hash.side_effect = Exception("Blockchain error")
    
    request_data = {
        "prompt": "Test prompt",
        "user_address": "0x123",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/prompts", json=request_data)
    assert response.status_code == 500
    assert "Blockchain error" in response.json()["detail"] 