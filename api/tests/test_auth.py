import pytest
from fastapi import status
import re
import logging
import time
from httpx import Timeout

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set a timeout for all requests
TIMEOUT = Timeout(5.0)  # 5 seconds timeout

def test_verify_signature_success(client, test_verification_data, mock_blockchain_service):
    """Test successful signature verification."""
    logger.debug("Starting test_verify_signature_success")
    logger.debug(f"Mock blockchain service: {mock_blockchain_service}")
    logger.debug(f"Test verification data: {test_verification_data}")
    
    start_time = time.time()
    try:
        response = client.post("/verify", json=test_verification_data, timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is True
        assert data["recovered_address"] == test_verification_data["expected_address"]
        assert data["match"] is True
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_verify_signature_invalid_hash(client, test_verification_data):
    """Test signature verification with invalid hash."""
    logger.debug("Starting test_verify_signature_invalid_hash")
    invalid_data = test_verification_data.copy()
    invalid_data["verification_hash"] = "invalid_hash"
    
    start_time = time.time()
    try:
        response = client.post("/verify", json=invalid_data, timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_verify_signature_invalid_signature(client, test_verification_data):
    """Test signature verification with invalid signature."""
    logger.debug("Starting test_verify_signature_invalid_signature")
    invalid_data = test_verification_data.copy()
    invalid_data["signature"] = "invalid_signature"
    
    start_time = time.time()
    try:
        response = client.post("/verify", json=invalid_data, timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_verify_signature_mismatch(client, test_verification_data, mock_blockchain_service):
    """Test signature verification with mismatched addresses."""
    logger.debug("Starting test_verify_signature_mismatch")
    mock_blockchain_service.verify_signature.return_value = False
    
    start_time = time.time()
    try:
        response = client.post("/verify", json=test_verification_data, timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is False
        assert data["match"] is False
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_verify_hash_success(client, mock_blockchain_service):
    """Test successful hash verification."""
    logger.debug("Starting test_verify_hash_success")
    test_hash = "0x" + "1" * 64
    
    start_time = time.time()
    try:
        response = client.get(f"/verify/hash/{test_hash}", timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "is_valid" in data
        assert "timestamp" in data
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_verify_hash_invalid_format(client):
    """Test hash verification with invalid format."""
    logger.debug("Starting test_verify_hash_invalid_format")
    invalid_hash = "invalid_hash"
    
    start_time = time.time()
    try:
        response = client.get(f"/verify/hash/{invalid_hash}", timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

def test_get_signer(client):
    """Test getting the signer address."""
    logger.debug("Starting test_get_signer")
    
    start_time = time.time()
    try:
        response = client.get("/signer", timeout=TIMEOUT)
        logger.debug(f"Request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "address" in data
        # Verify the address is a valid Ethereum address
        assert re.match(r'^0x[a-fA-F0-9]{40}$', data["address"])
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

'''
def test_wallet_address_validation(client, test_wallet_address):
    """Test wallet address validation in various endpoints."""
    logger.debug("Starting test_wallet_address_validation")
    
    # Test valid address
    start_time = time.time()
    try:
        response = client.post(
            "/sessions/create",
            json={"wallet_address": test_wallet_address},
            timeout=TIMEOUT
        )
        logger.debug(f"Valid address request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Valid address response status: {response.status_code}")
        logger.debug(f"Valid address response body: {response.text}")
        assert response.status_code == status.HTTP_200_OK

        # Test invalid address format
        start_time = time.time()
        invalid_address = "0xinvalid"
        response = client.post(
            "/sessions/create",
            json={"wallet_address": invalid_address},
            timeout=TIMEOUT
        )
        logger.debug(f"Invalid address request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Invalid address response status: {response.status_code}")
        logger.debug(f"Invalid address response body: {response.text}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test missing address
        start_time = time.time()
        response = client.post(
            "/sessions/create",
            json={},
            timeout=TIMEOUT
        )
        logger.debug(f"Missing address request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Missing address response status: {response.status_code}")
        logger.debug(f"Missing address response body: {response.text}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise
        
'''

def test_rate_limiting(client, test_wallet_address):
    """Test rate limiting functionality."""
    logger.debug("Starting test_rate_limiting")
    
    # Make multiple requests in quick succession
    for i in range(10):
        start_time = time.time()
        try:
            response = client.post(
                "/sessions/create",
                json={"wallet_address": test_wallet_address},
                timeout=TIMEOUT
            )
            logger.debug(f"Request {i+1} completed in {time.time() - start_time:.2f} seconds")
            logger.debug(f"Request {i+1} response status: {response.status_code}")
        except Exception as e:
            logger.error(f"Request {i+1} failed with error: {str(e)}")
            raise
    
    # The next request should be rate limited
    start_time = time.time()
    try:
        response = client.post(
            "/sessions/create",
            json={"wallet_address": test_wallet_address},
            timeout=TIMEOUT
        )
        logger.debug(f"Rate limited request completed in {time.time() - start_time:.2f} seconds")
        logger.debug(f"Rate limited response status: {response.status_code}")
        logger.debug(f"Rate limited response body: {response.text}")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    except Exception as e:
        logger.error(f"Rate limiting test failed with error: {str(e)}")
        raise 