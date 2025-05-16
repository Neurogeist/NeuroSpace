import pytest
from fastapi import status
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_list_models_success(client):
    """Test successful model listing."""
    logger.debug("Starting test_list_models_success")
    response = client.get("/models")
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], dict)  # Models are returned as a dict
    assert len(data["models"]) > 0
    # Check that we have the expected models
    assert "mixtral-8x7b-instruct" in data["models"]
    assert "gemma-2-27b-it" in data["models"]

def test_get_model_success(client):
    """Test successful model retrieval."""
    logger.debug("Starting test_get_model_success")
    # First get the list of models
    list_response = client.get("/models")
    assert list_response.status_code == status.HTTP_200_OK
    models = list_response.json()["models"]
    assert len(models) > 0
    
    # Then get details for the first model
    model_name = list(models.keys())[0]  # Get the first model name
    response = client.get(f"/models/{model_name}")
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "name" in data
    assert "description" in data
    assert "parameters" in data

def test_submit_prompt_success(client, test_session_id):
    """Test successful prompt submission."""
    logger.debug("Starting test_submit_prompt_success")
    prompt_data = {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "user_address": "0x1234567890123456789012345678901234567890",
        "session_id": test_session_id,
        "payment_method": "FREE"
    }
    response = client.post(
        "/submit_prompt",
        json=prompt_data
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert "model_id" in data
    assert "metadata" in data

def test_submit_prompt_invalid_model(client, test_session_id):
    """Test prompt submission with invalid model."""
    logger.debug("Starting test_submit_prompt_invalid_model")
    prompt_data = {
        "prompt": "Test prompt",
        "model": "invalid-model",
        "user_address": "0x1234567890123456789012345678901234567890",
        "session_id": test_session_id,
        "payment_method": "FREE"
    }
    response = client.post(
        "/submit_prompt",
        json=prompt_data
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_submit_prompt_invalid_parameters(client, test_session_id):
    """Test prompt submission with invalid parameters."""
    logger.debug("Starting test_submit_prompt_invalid_parameters")
    prompt_data = {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "user_address": "0x1234567890123456789012345678901234567890",
        "session_id": test_session_id,
        "payment_method": "INVALID"  # Invalid payment method
    }
    response = client.post(
        "/submit_prompt",
        json=prompt_data
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_prompt_status_success(client, test_session_id):
    """Test successful prompt status retrieval."""
    logger.debug("Starting test_get_prompt_status_success")
    # First submit a prompt
    prompt_data = {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    submit_response = client.post(
        f"/prompts/{test_session_id}",
        json=prompt_data
    )
    assert submit_response.status_code == status.HTTP_200_OK
    prompt_id = submit_response.json()["prompt_id"]
    
    # Then get the status
    response = client.get(f"/prompts/{prompt_id}/status")
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_cancel_prompt_success(client, test_session_id):
    """Test successful prompt cancellation."""
    logger.debug("Starting test_cancel_prompt_success")
    # First submit a prompt
    prompt_data = {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    submit_response = client.post(
        f"/prompts/{test_session_id}",
        json=prompt_data
    )
    assert submit_response.status_code == status.HTTP_200_OK
    prompt_id = submit_response.json()["prompt_id"]
    
    # Then cancel it
    response = client.post(f"/prompts/{prompt_id}/cancel")
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert data["status"] == "cancelled"

def test_prompt_rate_limiting(client, test_session_id):
    """Test prompt submission rate limiting."""
    logger.debug("Starting test_prompt_rate_limiting")
    prompt_data = {
        "prompt": "Test prompt",
        "model": "mixtral-8x7b-instruct",
        "user_address": "0x1234567890123456789012345678901234567890",
        "session_id": test_session_id,
        "payment_method": "FREE"
    }
    
    # Submit multiple prompts in quick succession
    for _ in range(10):
        response = client.post(
            "/submit_prompt",
            json=prompt_data
        )
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text}")
    
    # The next submission should be rate limited
    response = client.post(
        "/submit_prompt",
        json=prompt_data
    )
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS 