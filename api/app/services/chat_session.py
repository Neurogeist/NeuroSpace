from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Represents a single message in a chat session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    ipfs_cid: Optional[str] = Field(None, alias="ipfsHash")
    transaction_hash: Optional[str] = Field(None, alias="transactionHash")
    model_name: Optional[str] = None
    model_id: Optional[str] = Field(None, alias="modelId")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        alias_generator = lambda x: x.replace("_", "") if x.endswith(("_cid", "_hash", "_id")) else x
        populate_by_name = True

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

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_name: Optional[str] = None,
        model_id: Optional[str] = None,
        ipfs_cid: Optional[str] = None,
        transaction_hash: Optional[str] = None
    ) -> ChatMessage:
        """Add a message to a session."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
            session = self.sessions[session_id]

        # Create metadata dictionary
        metadata = {
            "model_name": model_name,
            "model_id": model_id,
            "ipfs_cid": ipfs_cid,
            "transaction_hash": transaction_hash,
            "timestamp": datetime.now().isoformat()
        }

        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            ipfs_cid=ipfs_cid,
            transaction_hash=transaction_hash,
            model_name=model_name,
            model_id=model_id,
            metadata=metadata
        )
        session.add_message(message)
        return message

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