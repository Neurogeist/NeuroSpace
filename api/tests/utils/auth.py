"""
Authentication utilities for testing.
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt as PyJWT
from ...app.core.config import get_settings

settings = get_settings()

def create_test_token(
    wallet_address: str = "0x1234567890abcdef1234567890abcdef12345678",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a test JWT token for testing purposes.
    
    Args:
        wallet_address: The wallet address to include in the token
        expires_delta: Optional expiration time delta (defaults to 24 hours)
        
    Returns:
        str: The generated JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
        
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": wallet_address,
        "exp": expire
    }
    
    encoded_jwt = PyJWT.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def verify_test_token(token: str) -> dict:
    """
    Verify a test JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        dict: The decoded token payload
        
    Raises:
        PyJWT.InvalidTokenError: If the token is invalid
    """
    try:
        payload = PyJWT.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except PyJWT.InvalidTokenError as e:
        raise PyJWT.InvalidTokenError(f"Invalid token: {str(e)}")

if __name__ == "__main__":
    # Example usage
    token = create_test_token()
    print(f"Test Token: {token}")
    
    # Verify the token
    try:
        payload = verify_test_token(token)
        print(f"Token payload: {payload}")
    except PyJWT.InvalidTokenError as e:
        print(f"Token verification failed: {str(e)}") 