from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    """Represents a single message in a chat session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    ipfs_cid: Optional[str] = Field(None, alias="ipfsHash")
    transaction_hash: Optional[str] = Field(None, alias="transactionHash")
    model_name: str
    model_id: str
    verification_hash: Optional[str] = Field(None, description="The hash of the prompt-response pair")
    signature: Optional[str] = Field(None, description="The digital signature of the verification hash")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        alias_generator = lambda x: x.replace("_", "") if x.endswith(("_cid", "_hash", "_id")) else x
        populate_by_name = True
        schema_extra = {
            "example": {
                "role": "assistant",
                "content": "Hello! How can I help you today?",
                "model_name": "mixtral-remote",
                "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "metadata": {
                    "timestamp": "2024-03-14T12:00:00",
                    "ipfs_cid": "QmXyZ...",
                    "transaction_hash": "0x123...",
                    "verification_hash": "abc123...",
                    "signature": "0x456...",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        }

    def dict(self, *args, **kwargs):
        """Override dict to ensure aliases are properly handled and only show links for assistant messages."""
        d = super().dict(*args, **kwargs)
        
        # Only include links for assistant messages
        if self.role == "assistant":
            if "ipfs_cid" in d:
                d["ipfsHash"] = d.pop("ipfs_cid")
            if "transaction_hash" in d:
                d["transactionHash"] = d.pop("transaction_hash")
            if "model_id" in d:
                d["modelId"] = d.pop("model_id")
        else:
            # Remove links for user messages
            d.pop("ipfs_cid", None)
            d.pop("transaction_hash", None)
            d.pop("model_id", None)
            d.pop("ipfsHash", None)
            d.pop("transactionHash", None)
            d.pop("modelId", None)
        
        return d

class ChatSession:
    """Represents a chat session with its messages."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, message: ChatMessage):
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages(self) -> List[ChatMessage]:
        """Get all messages in the session."""
        return self.messages

    def format_chat_history(self) -> str:
        """Format the chat history as a string for model input."""
        formatted_messages = []
        for msg in self.messages:
            role = "User" if msg.role == "user" else "Assistant"
            formatted_messages.append(f"{role}: {msg.content}")
        return "\n".join(formatted_messages)

class ChatSessionService:
    """Service for managing chat sessions."""
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> List[ChatSession]:
        """Get all chat sessions."""
        return list(self.sessions.values())

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_name: Optional[str] = None,
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to a chat session."""
        try:
            # Get the session
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Create the message with verification info if it's an assistant message
            message_metadata = metadata or {}
            if role == "assistant":
                # Extract transaction hash from metadata
                tx_hash = None
                if isinstance(metadata.get("transaction_hash"), dict):
                    tx_hash = metadata["transaction_hash"].get("transaction_hash")
                else:
                    tx_hash = metadata.get("transaction_hash")
                
                # Ensure verification info is included
                message_metadata.update({
                    "verification_hash": metadata.get("verification_hash"),
                    "signature": metadata.get("signature"),
                    "ipfs_cid": metadata.get("ipfs_cid"),
                    "transaction_hash": tx_hash
                })
            
            # Create the message
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                model_name=model_name,
                model_id=model_id,
                verification_hash=message_metadata.get("verification_hash"),
                signature=message_metadata.get("signature"),
                ipfs_cid=message_metadata.get("ipfs_cid"),
                transaction_hash=message_metadata.get("transaction_hash"),
                metadata=message_metadata
            )
            
            # Add the message to the session
            session.messages.append(message)
            session.updated_at = datetime.utcnow()
            
            # Save the session
            self.sessions[session_id] = session
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {str(e)}")
            raise

    def get_session_messages(self, session_id: str) -> Optional[List[ChatMessage]]:
        """Get all messages in a session."""
        session = self.get_session(session_id)
        if session:
            # Ensure all messages have metadata
            for message in session.messages:
                # Always ensure metadata is refreshed and consistent
                message.metadata = {
                    "model": message.model_name,
                    "model_id": message.model_id,
                    "ipfsHash": message.ipfs_cid,
                    "transactionHash": message.transaction_hash,
                    "temperature": message.metadata.get("temperature", 0.7) if message.metadata else 0.7,
                    "max_tokens": message.metadata.get("max_tokens", 512) if message.metadata else 512,
                    "top_p": message.metadata.get("top_p", 0.9) if message.metadata else 0.9,
                    "do_sample": message.metadata.get("do_sample", True) if message.metadata else True,
                    "num_beams": message.metadata.get("num_beams", 1) if message.metadata else 1,
                    "early_stopping": message.metadata.get("early_stopping", False) if message.metadata else False
                }
            return session.get_messages()
        return None

    def format_session_history(self, session_id: str) -> Optional[str]:
        """Format the chat history of a session as a string."""
        session = self.get_session(session_id)
        return session.format_chat_history() if session else None 