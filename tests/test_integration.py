import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_submit_and_get_prompt():
    # Submit a prompt
    prompt_data = {"prompt": "What is the capital of France?"}
    response = requests.post(f"{BASE_URL}/prompts", json=prompt_data)
    assert response.status_code == 200
    
    prompt_response = response.json()
    assert "prompt_id" in prompt_response
    assert prompt_response["prompt"] == prompt_data["prompt"]
    assert prompt_response["response"] is None
    assert not prompt_response["is_processed"]
    
    # Get the prompt status
    prompt_id = prompt_response["prompt_id"]
    get_response = requests.get(f"{BASE_URL}/prompts/{prompt_id}")
    assert get_response.status_code == 200
    
    # TODO: Add more comprehensive tests once the Solana integration is complete
    # This should include:
    # 1. Verifying the prompt is stored on-chain
    # 2. Checking that the response is processed and stored
    # 3. Validating the final state of the prompt account

if __name__ == "__main__":
    pytest.main([__file__]) 