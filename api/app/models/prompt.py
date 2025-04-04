from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
import re
from ..services.chat_session import ChatSession

class PromptRequest(BaseModel):
    """Request model for prompt submission."""
    prompt: str = Field(..., description="The prompt to generate a response for")
    model_name: Optional[str] = Field(None, description="The model to use for generation")
    session_id: Optional[str] = Field(None, description="The chat session ID. If not provided, a new session will be created")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the request")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "What's a good book to read?",
                "model_name": "tinyllama",
                "session_id": "session123",
                "timestamp": "2023-04-14T12:00:00"
            }
        }

class PromptResponse(BaseModel):
    """Response model for prompt generation."""
    response: str = Field(..., description="The generated response")
    model_name: str = Field(..., description="The model used for generation")
    model_id: str = Field(..., description="The full model ID from Hugging Face")
    session_id: str = Field(..., description="The chat session ID")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the response")

    class Config:
        schema_extra = {
            "example": {
                "response": "The Alchemist by Paulo Coelho is a great choice!",
                "model_name": "tinyllama",
                "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "session_id": "session123",
                "metadata": {
                    "timestamp": "2024-02-20T12:00:00",
                    "temperature": 0.7,
                    "max_tokens": 256
                }
            }
        }

class PromptMetadata(BaseModel):
    prompt: str
    response: str
    timestamp: datetime
    user_address: Optional[str] = None

class ChatMessage(BaseModel):
    """Model for a single chat message."""
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The content of the message")
    timestamp: datetime = Field(..., description="When the message was sent")
    model_name: Optional[str] = Field(None, description="The model used for generation")
    model_id: Optional[str] = Field(None, description="The full model ID from Hugging Face")
    ipfs_cid: Optional[str] = Field(None, description="The IPFS CID of the message")
    transaction_hash: Optional[str] = Field(None, description="The blockchain transaction hash")

class SessionResponse(BaseModel):
    """Response model for retrieving a chat session."""
    session_id: str = Field(..., description="The unique identifier for the chat session")
    messages: List[ChatMessage] = Field(..., description="List of messages in the session")
    created_at: datetime = Field(..., description="When the session was created")
    updated_at: datetime = Field(..., description="When the session was last updated")
    
    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        },
        "protected_namespaces": ()
    }
        
    @classmethod
    def from_chat_session(cls, session: ChatSession) -> "SessionResponse":
        """Create a SessionResponse from a ChatSession."""
        return cls(
            session_id=session.session_id,
            messages=[msg.dict() for msg in session.messages],
            created_at=session.created_at,
            updated_at=session.updated_at
        ) 