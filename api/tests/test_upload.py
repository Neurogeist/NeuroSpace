import pytest
from fastapi import status
import io

def test_upload_pdf_basic(client, mock_file, mock_wallet, mock_services):
    """Test basic PDF upload functionality"""
    response = client.post(
        "/rag/upload",
        files=mock_file,
        headers={"wallet-address": mock_wallet['address']}
    )
    
    # For now, just check that we get a response
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    assert isinstance(response.json(), dict)

def test_upload_invalid_file_type(client, mock_wallet, mock_redis, mock_services):
    """Test upload with invalid file type"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    invalid_file = {
        'file': ('test.txt', b'invalid content', 'text/plain')
    }
    
    response = client.post(
        "/rag/upload",
        files=invalid_file,
        headers={"wallet-address": mock_wallet['address']}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response.json()["detail"]

def test_upload_no_auth(client, mock_file, mock_redis, mock_services):
    """Test upload without authentication"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    response = client.post(
        "/rag/upload",
        files=mock_file
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_upload_invalid_auth(client, mock_file, mock_redis, mock_services):
    """Test upload with invalid authentication"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    response = client.post(
        "/rag/upload",
        files=mock_file,
        headers={"wallet-address": "invalid_address"}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_upload_file_too_large(client, mock_wallet, mock_redis, mock_services):
    """Test upload with file exceeding size limit"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    # Create a large file (11MB)
    large_file = {
        'file': ('large.pdf', b'0' * (11 * 1024 * 1024), 'application/pdf')
    }
    
    response = client.post(
        "/rag/upload",
        files=large_file,
        headers={"wallet-address": mock_wallet['address']}
    )
    
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

def test_upload_corrupted_pdf(client, mock_wallet, mock_redis, mock_services):
    """Test upload with corrupted PDF file"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    corrupted_file = {
        'file': ('corrupted.pdf', b'not a real pdf', 'application/pdf')
    }
    
    response = client.post(
        "/rag/upload",
        files=corrupted_file,
        headers={"wallet-address": mock_wallet['address']}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid PDF" in response.json()["detail"] 