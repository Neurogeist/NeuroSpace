import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
HEADERS = {
    "X-User-Address": "0x1234567890123456789012345678901234567890"
}

def test_chat_session():
    """Test chat session functionality."""
    session_id = None
    
    # Test 1: Create new session with first prompt
    print("\nTest 1: Creating new session")
    response = submit_prompt("What is the capital of France?")
    session_id = response["session_id"]
    print(f"Created session: {session_id}")
    print(f"Response: {response['response']}")
    
    # Test 2: Continue conversation in same session
    print("\nTest 2: Continuing conversation")
    response = submit_prompt("What is its population?", session_id)
    print(f"Response: {response['response']}")
    
    # Test 3: Get session history
    print("\nTest 3: Retrieving session history")
    history = get_session_history(session_id)
    print(f"Session has {len(history['messages'])} messages")
    for msg in history["messages"]:
        print(f"{msg['role']}: {msg['content']}")
    
    # Test 4: Start new session with different model
    print("\nTest 4: Starting new session with different model")
    response = submit_prompt("What is the tallest mountain?", model_name="phi")
    new_session_id = response["session_id"]
    print(f"Created new session: {new_session_id}")
    print(f"Response: {response['response']}")
    
    # Test 5: Get list of all sessions (if implemented)
    print("\nTest 5: Getting all sessions")
    try:
        sessions = get_all_sessions()
        print(f"Found {len(sessions)} sessions")
    except:
        print("Get all sessions endpoint not implemented")

def submit_prompt(prompt: str, session_id: str = None, model_name: str = "tinyllama") -> Dict[str, Any]:
    """Submit a prompt and return the response."""
    data = {
        "prompt": prompt,
        "model_name": model_name
    }
    if session_id:
        data["session_id"] = session_id
    
    response = requests.post(
        f"{BASE_URL}/prompt",
        json=data,
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()

def get_session_history(session_id: str) -> Dict[str, Any]:
    """Get the history of a session."""
    response = requests.get(
        f"{BASE_URL}/sessions/{session_id}",
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()

def get_all_sessions() -> Dict[str, Any]:
    """Get all sessions (if implemented)."""
    response = requests.get(
        f"{BASE_URL}/sessions",
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    test_chat_session() 