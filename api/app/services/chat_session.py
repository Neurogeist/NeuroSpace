from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging
from sqlalchemy.orm import Session
from ..models.chat import ChatSessionDB, ChatMessageDB
from ..models.database import SessionLocal

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
    id: Optional[str] = None

    model_config = {
        'populate_by_name': True,
        'json_encoders': {
            datetime: lambda dt: dt.isoformat()
        },
        'protected_namespaces': (),
        'json_schema_extra': {
            'example': {
                'role': 'assistant',
                'content': 'Hello! How can I help you today?',
                'model_name': 'mixtral-8x7b-instruct',
                'model_id': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                'metadata': {
                    'timestamp': '2024-03-14T12:00:00',
                    'ipfs_cid': 'QmXyZ...',
                    'transaction_hash': '0x123...',
                    'verification_hash': 'abc123...',
                    'signature': '0x456...',
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            }
        }
    }

    def dict(self, *args, **kwargs):
        """Override dict to ensure aliases are properly handled and always include metadata."""
        data = super().dict(*args, **kwargs)

        # Convert timestamp to ISO string
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat().replace("+00:00", "Z")

        # Convert UUID to string if present
        if isinstance(data.get('id'), uuid.UUID):
            data['id'] = str(data['id'])

        data["metadata"] = self.metadata

        if self.role == "assistant":
            if "ipfs_cid" in data:
                data["ipfsHash"] = data.pop("ipfs_cid")
            if "transaction_hash" in data:
                data["transactionHash"] = data.pop("transaction_hash")
            if "model_id" in data:
                data["modelId"] = data.pop("model_id")
        else:
            data.pop("ipfsHash", None)
            data.pop("transactionHash", None)
            data.pop("modelId", None)
            data.pop("ipfs_cid", None)
            data.pop("transaction_hash", None)
            data.pop("model_id", None)

        return data


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
        self.db = SessionLocal()

    def _get_new_session(self):
        """Get a new database session."""
        self.db.close()
        self.db = SessionLocal()
        return self.db

    def create_session(self, session_id: Optional[str] = None, wallet_address: Optional[str] = None) -> str:
        """Create a new chat session."""
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Create new session in database
            db_session = ChatSessionDB(
                id=uuid.UUID(session_id),
                wallet_address=wallet_address or "unknown"
            )
            self.db.add(db_session)
            self.db.commit()
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            raise

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        try:
            db_session = self.db.query(ChatSessionDB).filter(ChatSessionDB.id == uuid.UUID(session_id)).first()
            if not db_session:
                return None

            session = ChatSession(session_id)
            session.created_at = db_session.created_at
            session.updated_at = db_session.updated_at or db_session.created_at

            db_messages = self.db.query(ChatMessageDB).filter(
                ChatMessageDB.session_id == uuid.UUID(session_id)
            ).order_by(ChatMessageDB.timestamp).all()

            for db_msg in db_messages:
                message = ChatMessage(
                    role=db_msg.role,
                    content=db_msg.content,
                    timestamp=db_msg.timestamp,
                    model_name=db_msg.model_name,
                    model_id=db_msg.model_id,
                    ipfs_cid=db_msg.ipfs_cid,
                    transaction_hash=db_msg.transaction_hash,
                    verification_hash=db_msg.verification_hash,
                    signature=db_msg.signature,
                    metadata=db_msg.message_metadata or {}
                )
                session.add_message(message)

            return session

        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            return None

    def get_all_sessions(self, wallet_address: Optional[str] = None) -> List[ChatSession]:
        try:
            query = self.db.query(ChatSessionDB)
            if wallet_address:
                query = query.filter(ChatSessionDB.wallet_address == wallet_address)
            db_sessions = query.all()
            sessions = []

            for db_session in db_sessions:
                session = self.get_session(str(db_session.id))
                if session:
                    sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Error getting all sessions: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            return []

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_name: str,
        model_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        try:
            db_session = self.db.query(ChatSessionDB).filter(
                ChatSessionDB.id == uuid.UUID(session_id)
            ).first()
            if not db_session:
                raise ValueError(f"Session {session_id} not found")

            # Update session title if it's the first message
            if not db_session.title and role == "user":
                # Set title based on first user message
                db_session.title = content[:50] + "..." if len(content) > 50 else content

            # Always update updated_at when any new message is added
            db_session.updated_at = datetime.now(timezone.utc)
            self.db.add(db_session)

            message_metadata = metadata or {}

            tx_hash = None
            if isinstance(metadata.get("transaction_hash"), dict):
                tx_hash = metadata["transaction_hash"].get("transaction_hash")
            else:
                tx_hash = metadata.get("transaction_hash")

            if metadata and (metadata.get("verification_hash") or metadata.get("signature")):
                message_metadata.update({
                    "verification_hash": metadata.get("verification_hash"),
                    "signature": metadata.get("signature"),
                    "ipfs_cid": metadata.get("ipfs_cid"),
                    "transaction_hash": tx_hash
                })

            timestamp = metadata.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif isinstance(timestamp, datetime):
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)

            db_message = ChatMessageDB(
                session_id=uuid.UUID(session_id),
                role=role,
                content=content,
                timestamp=timestamp,
                model_name=model_name,
                model_id=model_id,
                ipfs_cid=message_metadata.get("ipfs_cid"),
                transaction_hash=message_metadata.get("transaction_hash"),
                verification_hash=message_metadata.get("verification_hash"),
                signature=message_metadata.get("signature"),
                message_metadata=message_metadata
            )

            self.db.add(db_message)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            raise

    def get_session_messages(self, session_id: str) -> Optional[List[ChatMessage]]:
        try:
            db_messages = self.db.query(ChatMessageDB).filter(
                ChatMessageDB.session_id == uuid.UUID(session_id)
            ).order_by(ChatMessageDB.timestamp).all()

            messages = []
            for db_msg in db_messages:
                if db_msg.message_metadata is None:
                    db_msg.message_metadata = {}
                
                # Update metadata with all fields
                db_msg.message_metadata.update({
                    "model": db_msg.model_name,
                    "model_id": db_msg.model_id,
                    "ipfs_cid": db_msg.ipfs_cid,
                    "transaction_hash": db_msg.transaction_hash,
                    "verification_hash": db_msg.verification_hash,
                    "signature": db_msg.signature,
                    "temperature": db_msg.message_metadata.get("temperature", 0.7),
                    "max_tokens": db_msg.message_metadata.get("max_tokens", 512),
                    "top_p": db_msg.message_metadata.get("top_p", 0.9),
                    "do_sample": db_msg.message_metadata.get("do_sample", True),
                    "num_beams": db_msg.message_metadata.get("num_beams", 1),
                    "early_stopping": db_msg.message_metadata.get("early_stopping", False),
                    "timestamp": db_msg.timestamp.isoformat().replace("+00:00", "Z"),
                    "original_prompt": db_msg.message_metadata.get("original_prompt", ""),
                    "wallet_address": db_msg.message_metadata.get("wallet_address", ""),
                    "session_id": db_msg.message_metadata.get("session_id", ""),
                    "system_prompt": db_msg.message_metadata.get("system_prompt", None)
                })

                message = ChatMessage(
                    id=str(db_msg.id),  # Convert UUID to string
                    role=db_msg.role,
                    content=db_msg.content,
                    timestamp=db_msg.timestamp,
                    model_name=db_msg.model_name or "unknown",
                    model_id=db_msg.model_id or "unknown",
                    metadata=db_msg.message_metadata
                )
                messages.append(message)

            return messages

        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            return None

    def format_session_history(self, session_id: str) -> Optional[str]:
        session = self.get_session(session_id)
        return session.format_chat_history() if session else None

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages."""
        try:
            # First delete all messages in the session
            self.db.query(ChatMessageDB).filter(
                ChatMessageDB.session_id == uuid.UUID(session_id)
            ).delete()

            # Then delete the session itself
            self.db.query(ChatSessionDB).filter(
                ChatSessionDB.id == uuid.UUID(session_id)
            ).delete()

            self.db.commit()
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            self.db.rollback()
            self._get_new_session()
            raise
