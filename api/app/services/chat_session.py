from typing import Dict, List, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel

class ChatMessage(BaseModel):
    """Represents a single message in a chat session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    ipfs_cid: Optional[str] = None
    transaction_hash: Optional[str] = None

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

        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            model_name=model_name,
            model_id=model_id,
            ipfs_cid=ipfs_cid,
            transaction_hash=transaction_hash
        )
        session.add_message(message)
        return message

    def get_session_messages(self, session_id: str) -> Optional[List[ChatMessage]]:
        """Get all messages in a session."""
        session = self.get_session(session_id)
        return session.get_messages() if session else None

    def format_session_history(self, session_id: str) -> Optional[str]:
        """Format the chat history of a session as a string."""
        session = self.get_session(session_id)
        return session.format_chat_history() if session else None 