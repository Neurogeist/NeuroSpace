import hashlib
import json
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def _serialize_value(value: Any) -> str:
    """Serialize a value to a stable string representation."""
    if isinstance(value, float):
        # Use fixed precision for floats
        return f"{value:.6f}"
    elif isinstance(value, datetime):
        # Use ISO format for timestamps without microseconds
        return value.replace(microsecond=0).isoformat()
    elif isinstance(value, (list, tuple)):
        # Serialize lists and tuples
        items = [_serialize_value(item) for item in value]
        return f"[{','.join(items)}]"
    elif isinstance(value, dict):
        # Recursively serialize dictionaries
        return _serialize_dict(value)
    elif value is None:
        return "null"
    else:
        # Convert other types to string and escape special characters
        return json.dumps(str(value))

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
    
    logger.info(f"📝 Backend verification data: {data_copy}")
    logger.info(f"📝 Backend serialized data: {serialized_data}")
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(serialized_data.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    logger.info(f"🔐 Backend generated hash: {hash_hex}")
    return hash_hex

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
        logger.info(f"🔍 Expected hash: {expected_hash}")
        computed_hash = generate_verification_hash(data)
        logger.info(f"🔍 Computed hash: {computed_hash}")
        logger.info(f"🔍 Hash match: {computed_hash == expected_hash}")
        return computed_hash == expected_hash
    except Exception as e:
        logger.error(f"Error verifying hash: {str(e)}")
        return False 