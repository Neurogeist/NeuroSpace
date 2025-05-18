from fastapi import HTTPException, Depends, Header, Request, status
from eth_account import Account
from eth_account.messages import encode_defunct
from typing import Optional
import logging
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from web3 import Web3
from .config import settings

logger = logging.getLogger(__name__)

class WalletAuthError(Exception):
    """Base exception for wallet authentication errors."""
    pass

class InvalidSignatureError(WalletAuthError):
    """Raised when signature verification fails."""
    pass

class MissingAuthHeadersError(WalletAuthError):
    """Raised when required auth headers are missing."""
    pass

# Security scheme for JWT
security = HTTPBearer()

class TokenData(BaseModel):
    wallet_address: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_wallet_signature(wallet_address: str, signature: str, nonce: str) -> bool:
    """
    Verify a wallet signature using eth_account.
    
    Args:
        wallet_address: The Ethereum wallet address
        signature: The signature to verify
        nonce: The nonce used in the signature
        
    Returns:
        bool: True if signature is valid, False otherwise
        
    Raises:
        InvalidSignatureError: If signature verification fails
    """
    try:
        # Create the message that was signed
        message = f"Sign this message to authenticate with NeuroSpace. Nonce: {nonce}"
        message_encoded = encode_defunct(text=message)
        
        # Recover the address from the signature
        recovered_address = Account.recover_message(message_encoded, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == wallet_address.lower()
        
    except Exception as e:
        logger.error(f"Error verifying wallet signature: {str(e)}")
        raise InvalidSignatureError("Invalid signature")

async def require_wallet_auth(
    request: Request,
    wallet_address: str = Header(..., description="Ethereum wallet address"),
    wallet_signature: str = Header(..., description="Wallet signature"),
    wallet_nonce: str = Header(..., description="Nonce used in signature")
) -> str:
    """
    FastAPI dependency for wallet authentication.
    
    Args:
        request: The FastAPI request object
        wallet_address: The wallet address from the header
        wallet_signature: The signature from the header
        wallet_nonce: The nonce from the header
        
    Returns:
        str: The authenticated wallet address
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        if not verify_wallet_signature(wallet_address, wallet_signature, wallet_nonce):
            raise HTTPException(
                status_code=401,
                detail="Invalid wallet signature"
            )
        return wallet_address.lower()
        
    except MissingAuthHeadersError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except InvalidSignatureError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in wallet authentication: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 15 minutes if no expiration is provided
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm="HS256"
    )
    return encoded_jwt

def verify_wallet_signature_for_login(wallet_address: str, signature: str, nonce: str) -> bool:
    """Verify the Ethereum signature for login."""
    try:
        message = f"Login to NeuroSpace. Nonce: {nonce}"
        message_hash = encode_defunct(text=message)
        recovered_address = Web3().eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == wallet_address.lower()
    except Exception as e:
        logger.error(f"Signature verification failed: {str(e)}")
        return False

async def require_jwt_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Dependency for JWT authentication."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=["HS256"]
        )
        wallet_address: str = payload.get("sub")
        if wallet_address is None:
            raise credentials_exception
        return TokenData(wallet_address=wallet_address)
    except JWTError:
        raise credentials_exception 