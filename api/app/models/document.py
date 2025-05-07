from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import UUIDType
from pgvector.sqlalchemy import Vector
from datetime import datetime
from .database import Base
import uuid

class DocumentChunk(Base):
    """Model for storing document chunks with embeddings."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    ipfs_hash = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

class DocumentUpload(Base):
    """Model for tracking document uploads."""
    __tablename__ = "document_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    ipfs_hash = Column(String, nullable=False)
    wallet_address = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentUpload(id={self.id}, document_id={self.document_id}, name={self.name})>"
