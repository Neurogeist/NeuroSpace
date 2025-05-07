from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .database import Base

class FlaggedMessage(Base):
    __tablename__ = "flagged_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"))
    reason = Column(String, nullable=False)
    note = Column(Text)
    wallet_address = Column(String)
    flagged_at = Column(DateTime, default=datetime.utcnow) 