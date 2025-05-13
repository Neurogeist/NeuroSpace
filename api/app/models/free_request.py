from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid

class FreeRequest(Base):
    """Model for tracking free requests per wallet address."""
    __tablename__ = "free_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address = Column(String, nullable=False, unique=True)
    remaining_requests = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FreeRequest(wallet_address={self.wallet_address}, remaining_requests={self.remaining_requests})>" 