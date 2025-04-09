import hashlib
import json
from typing import Dict, Any
from datetime import datetime

def _serialize_value(value: Any) -> str:
    """Serialize a value to a stable string representation."""
    if isinstance(value, float):
        # Use fixed precision for floats
        return f"{value:.6f}"
    elif isinstance(value, datetime):
        # Use ISO format for timestamps
        return value.isoformat()
    elif isinstance(value, dict):
        # Recursively serialize dictionaries
        return _serialize_dict(value)
    else:
        # Convert other types to string
        return str(value)

def _serialize_dict(data: Dict[str, Any]) -> str:
    """Serialize a dictionary with sorted keys and stable value formatting."""
    # Sort keys to ensure consistent ordering
    sorted_items = sorted(data.items())
    # Serialize each key-value pair
    serialized_items = []
    for key, value in sorted_items:
        serialized_value = _serialize_value(value)
        serialized_items.append(f'"{key}":{serialized_value}')
    # Join with commas and wrap in braces
    return "{" + ",".join(serialized_items) + "}"

def generate_verification_hash(data: Dict[str, Any]) -> str:
    """
    Generate a verification hash for the given data.
    
    Args:
        data: Dictionary containing:
            - prompt: str
            - response: str
            - model_name: str
            - model_id: str
            - temperature: float
            - max_tokens: int
            - timestamp: datetime
    
    Returns:
        str: SHA-256 hash as a hex string
    """
    # Create a copy of the data to avoid modifying the original
    data_copy = data.copy()
    
    # Ensure all required fields are present
    required_fields = {
        "prompt", "response", "model_name", "model_id",
        "temperature", "max_tokens", "timestamp"
    }
    missing_fields = required_fields - set(data_copy.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Serialize the data with stable formatting
    serialized_data = _serialize_dict(data_copy)
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(serialized_data.encode('utf-8'))
    return hash_obj.hexdigest()

def verify_hash(data: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify that the data matches the expected hash.
    
    Args:
        data: Dictionary containing the data to verify
        expected_hash: The expected hash to compare against
    
    Returns:
        bool: True if the hash matches, False otherwise
    """
    try:
        computed_hash = generate_verification_hash(data)
        return computed_hash == expected_hash
    except Exception:
        return False 