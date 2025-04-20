from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import uuid

class ChatSessionDB(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    title = Column(Text, nullable=True)

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    model_name = Column(Text, nullable=True)
    model_id = Column(Text, nullable=True)
    ipfs_cid = Column(Text, nullable=True)
    transaction_hash = Column(Text, nullable=True)
    verification_hash = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)
    message_metadata = Column(JSON, nullable=True) 
 