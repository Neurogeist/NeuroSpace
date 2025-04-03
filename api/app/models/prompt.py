from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re

class PromptRequest(BaseModel):
    """Request model for prompt submission."""
    prompt: str = Field(..., description="The prompt to process")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the request")

class PromptResponse(BaseModel):
    """Response model for prompt submission."""
    response: str = Field(..., description="The generated response")
    ipfs_cid: str = Field(..., description="IPFS CID of the stored data")
    signature: str = Field(..., description="Transaction signature")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the response")
    user_address: str = Field(..., description="User's Ethereum address")
    
    class Config:
        schema_extra = {
            "example": {
                "response": "The capital of France is Paris.",
                "ipfs_cid": "QmExample123...",
                "signature": "0x123...",
                "timestamp": "2023-04-14T12:00:00",
                "user_address": "0x1234567890123456789012345678901234567890"
            }
        }

class PromptMetadata(BaseModel):
    prompt: str
    response: str
    timestamp: datetime
    user_address: Optional[str] = None 