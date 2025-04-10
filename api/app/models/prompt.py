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
    temperature: float = Field(default=0.7, description="Sampling temperature for generation")
    max_tokens: int = Field(default=512, description="Maximum number of tokens to generate")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to override the default")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "What's a good book to read?",
                "model_name": "tinyllama",
                "session_id": "session123",
                "timestamp": "2023-04-14T12:00:00",
                "temperature": 0.7,
                "max_tokens": 512,
                "system_prompt": "You are a helpful AI assistant. Answer questions accurately and concisely."
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
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "response": "The Alchemist by Paulo Coelho is a great choice!",
                "model_name": "tinyllama",
                "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "session_id": "session123",
                "metadata": {
                    "timestamp": "2024-02-20T12:00:00",
                    "model_name": "tinyllama",
                    "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "temperature": 0.7,
                    "max_tokens": 256,
                    "verification_hash": "abc123...",
                    "ipfs_cid": "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
                    "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
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
    model_id: Optional[str] = Field(None, alias="modelId", description="The full model ID from Hugging Face")
    ipfs_cid: Optional[str] = Field(None, alias="ipfsHash", description="The IPFS CID of the message")
    transaction_hash: Optional[str] = Field(None, alias="transactionHash", description="The blockchain transaction hash")
    verification_hash: Optional[str] = Field(None, description="The hash of the prompt-response pair")
    signature: Optional[str] = Field(None, description="The digital signature of the verification hash")

    class Config:
        allow_population_by_field_name = True

class SessionResponse(BaseModel):
    """Response model for retrieving a chat session."""
    session_id: str = Field(..., description="The unique identifier for the chat session")
    messages: List[ChatMessage] = Field(..., description="List of messages in the session")
    created_at: datetime = Field(..., description="When the session was created")
    updated_at: datetime = Field(..., description="When the session was last updated")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        protected_namespaces = ()
        
    @classmethod
    def from_chat_session(cls, session: ChatSession) -> "SessionResponse":
        """Create a SessionResponse from a ChatSession."""
        # Convert messages to dict with aliases
        messages = []
        for msg in session.messages:
            # Convert message to dict with aliases
            msg_dict = msg.dict(by_alias=True)
            
            # Include verification data if it exists
            if msg.verification_hash or msg.signature:
                msg_dict.update({
                    "model": msg.model_name,
                    "model_id": msg.model_id,
                    "timestamp": msg.timestamp.isoformat(),
                    "verification_hash": msg.verification_hash,
                    "signature": msg.signature,
                    "ipfs_cid": msg.ipfs_cid,
                    "transaction_hash": msg.transaction_hash
                })
            
            messages.append(msg_dict)
        
        return cls(
            session_id=session.session_id,
            messages=messages,
            created_at=session.created_at,
            updated_at=session.updated_at
        ) 