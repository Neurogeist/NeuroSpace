import pytest
from unittest.mock import Mock, patch
from api.app.services.ipfs import IPFSService
from api.tests.test_config import TestSettings

@pytest.fixture
def ipfs_service():
    with patch('api.app.services.ipfs.get_settings', return_value=TestSettings()):
        service = IPFSService()
        return service

def test_ipfs_initialization(ipfs_service):
    """Test that IPFS service initializes correctly."""
    assert ipfs_service.api_key is not None
    assert ipfs_service.api_secret is not None
    assert ipfs_service.jwt_token is not None

@pytest.mark.asyncio
async def test_upload_to_ipfs(ipfs_service):
    """Test uploading data to IPFS."""
    with patch('api.app.services.ipfs.requests.post') as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "IpfsHash": "QmTest123...",
            "PinSize": 100,
            "Timestamp": "2024-02-20T12:00:00"
        }
        mock_post.return_value = mock_response
        
        # Test data upload
        data = {
            "prompt": "What is the capital of France?",
            "response": "Paris",
            "timestamp": "2024-02-20T12:00:00"
        }
        
        result = await ipfs_service.upload_to_ipfs(data)
        assert result["IpfsHash"] == "QmTest123..."
        assert result["PinSize"] == 100
        assert result["Timestamp"] == "2024-02-20T12:00:00"

@pytest.mark.asyncio
async def test_upload_to_ipfs_error(ipfs_service):
    """Test error handling when uploading to IPFS."""
    with patch('api.app.services.ipfs.requests.post') as mock_post:
        # Mock failed response
        mock_post.side_effect = Exception("IPFS upload failed")
        
        # Test error handling
        data = {"test": "data"}
        with pytest.raises(Exception) as exc_info:
            await ipfs_service.upload_to_ipfs(data)
        assert "IPFS upload failed: IPFS upload failed" in str(exc_info.value) 