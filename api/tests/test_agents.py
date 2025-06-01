"""
Tests for the agent endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from ..app.main import app
from ..app.services.agent_registry import AgentRegistry, AgentConfig
from ..app.agents.onchain_qa import OnChainQAAgent
from .utils.auth import create_test_token

client = TestClient(app)

# Create a test token
TEST_TOKEN = create_test_token()

# Mock agent configuration
MOCK_AGENT_CONFIG = AgentConfig(
    agent_id="onchain_qa",
    display_name="On-Chain QA Agent",
    description="Answers questions about on-chain data",
    capabilities=["query_erc20_tokens", "get_token_balances"],
    required_config={"web3_provider": "WEB3_PROVIDER"},
    example_queries=["What is the total supply of USDC?"],
    max_concurrent_requests=10,
    rate_limit_per_minute=60,
    is_available=True
)

# Mock query response
MOCK_QUERY_RESPONSE = {
    "answer": "The total supply of USDC is 1,000,000",
    "trace_id": "test-trace-id",
    "ipfs_hash": "test-ipfs-hash",
    "commitment_hash": "test-commitment-hash",
    "trace_metadata": {
        "steps": [],
        "start_time": datetime.utcnow().isoformat()
    }
}

@pytest.fixture
def mock_agent_registry():
    """Fixture to mock the agent registry."""
    with patch("app.routers.agents.agent_registry") as mock:
        # Mock get_available_agents
        mock.get_available_agents.return_value = {
            "onchain_qa": MOCK_AGENT_CONFIG
        }
        
        # Mock get_agent_config
        mock.get_agent_config.return_value = MOCK_AGENT_CONFIG
        
        # Mock get_agent_class
        mock.get_agent_class.return_value = OnChainQAAgent
        
        # Mock get_agent_capabilities
        mock.get_agent_capabilities.return_value = MOCK_AGENT_CONFIG.capabilities
        
        # Mock get_example_queries
        mock.get_example_queries.return_value = MOCK_AGENT_CONFIG.example_queries
        
        yield mock

@pytest.fixture
def mock_agent():
    """Fixture to mock the agent instance."""
    with patch("app.agents.onchain_qa.OnChainQAAgent") as mock:
        # Mock initialize
        mock.initialize = AsyncMock()
        
        # Mock execute
        mock.execute = AsyncMock(return_value=MOCK_QUERY_RESPONSE)
        
        # Mock cleanup
        mock.cleanup = AsyncMock()
        
        yield mock

def test_list_agents(mock_agent_registry):
    """Test listing all available agents."""
    response = client.get(
        "/agents/",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["agent_id"] == "onchain_qa"
    assert data[0]["display_name"] == "On-Chain QA Agent"
    assert data[0]["capabilities"] == MOCK_AGENT_CONFIG.capabilities

def test_get_agent(mock_agent_registry):
    """Test getting a specific agent's details."""
    response = client.get(
        "/agents/onchain_qa",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "onchain_qa"
    assert data["display_name"] == "On-Chain QA Agent"
    assert data["capabilities"] == MOCK_AGENT_CONFIG.capabilities

def test_get_nonexistent_agent(mock_agent_registry):
    """Test getting a non-existent agent."""
    mock_agent_registry.get_agent_config.return_value = None
    
    response = client.get(
        "/agents/nonexistent",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_query_agent(mock_agent_registry, mock_agent):
    """Test querying an agent."""
    response = client.post(
        "/agents/query",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "What is the total supply of USDC?",
            "agent_id": "onchain_qa"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == MOCK_QUERY_RESPONSE["answer"]
    assert data["trace_id"] == MOCK_QUERY_RESPONSE["trace_id"]
    assert data["ipfs_hash"] == MOCK_QUERY_RESPONSE["ipfs_hash"]
    assert data["commitment_hash"] == MOCK_QUERY_RESPONSE["commitment_hash"]

def test_query_unavailable_agent(mock_agent_registry):
    """Test querying an unavailable agent."""
    mock_config = MOCK_AGENT_CONFIG.copy()
    mock_config.is_available = False
    mock_agent_registry.get_agent_config.return_value = mock_config
    
    response = client.post(
        "/agents/query",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "What is the total supply of USDC?",
            "agent_id": "onchain_qa"
        }
    )
    
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()

def test_get_agent_capabilities(mock_agent_registry):
    """Test getting agent capabilities."""
    response = client.get(
        "/agents/onchain_qa/capabilities",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data == MOCK_AGENT_CONFIG.capabilities

def test_get_agent_examples(mock_agent_registry):
    """Test getting agent example queries."""
    response = client.get(
        "/agents/onchain_qa/examples",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data == MOCK_AGENT_CONFIG.example_queries

def test_unauthorized_access():
    """Test accessing endpoints without authentication."""
    # Test list agents
    response = client.get("/agents/")
    assert response.status_code == 401
    
    # Test get agent
    response = client.get("/agents/onchain_qa")
    assert response.status_code == 401
    
    # Test query agent
    response = client.post(
        "/agents/query",
        json={
            "query": "What is the total supply of USDC?",
            "agent_id": "onchain_qa"
        }
    )
    assert response.status_code == 401
    
    # Test get capabilities
    response = client.get("/agents/onchain_qa/capabilities")
    assert response.status_code == 401
    
    # Test get examples
    response = client.get("/agents/onchain_qa/examples")
    assert response.status_code == 401

def test_invalid_query_request():
    """Test querying with invalid request data."""
    # Test empty query
    response = client.post(
        "/agents/query",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "",
            "agent_id": "onchain_qa"
        }
    )
    assert response.status_code == 422
    
    # Test missing agent_id
    response = client.post(
        "/agents/query",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "What is the total supply of USDC?"
        }
    )
    assert response.status_code == 422
    
    # Test query too long
    response = client.post(
        "/agents/query",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "x" * 1001,  # Exceeds max_length=1000
            "agent_id": "onchain_qa"
        }
    )
    assert response.status_code == 422 