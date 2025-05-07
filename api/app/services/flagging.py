from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from ..models.flagged_message import FlaggedMessage
from ..models.chat import ChatMessageDB
from ..models.database import SessionLocal
import uuid

logger = logging.getLogger(__name__)

class FlaggingService:
    def __init__(self):
        self.valid_reasons = {'hallucination', 'inappropriate', 'inaccurate', 'other'}
        self.db = SessionLocal()

    def _get_new_session(self):
        """Get a new database session."""
        self.db.close()
        self.db = SessionLocal()
        return self.db

    def flag_message(
        self,
        message_id: str,
        reason: str,
        wallet_address: str,
        note: Optional[str] = None
    ) -> FlaggedMessage:
        """Flag a message for moderation."""
        logger.info(f"Flagging message {message_id} by {wallet_address} for reason: {reason}")
        
        # Validate reason
        if reason not in self.valid_reasons:
            raise ValueError(f"Invalid reason. Must be one of: {', '.join(self.valid_reasons)}")
        
        try:
            message_uuid = uuid.UUID(message_id)
        except ValueError as e:
            raise ValueError(f"Invalid message ID format: {str(e)}")
        
        # Check if message exists
        message = self.db.query(ChatMessageDB).filter(ChatMessageDB.id == message_uuid).first()
        if not message:
            raise ValueError(f"Message not found: {message_id}")
        
        # Create flagged message
        flagged_message = FlaggedMessage(
            message_id=message_uuid,
            reason=reason,
            note=note,
            wallet_address=wallet_address.lower()  # Standardize wallet address
        )
        
        self.db.add(flagged_message)
        self.db.commit()
        self.db.refresh(flagged_message)
        
        return flagged_message

    def get_flagged_messages(
        self,
        wallet_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> List[FlaggedMessage]:
        """Get flagged messages with optional filtering."""
        try:
            query = self.db.query(FlaggedMessage)

            if wallet_address:
                query = query.filter(FlaggedMessage.wallet_address == wallet_address.lower())
            if reason:
                if reason not in self.valid_reasons:
                    raise ValueError(f"Invalid reason. Must be one of: {', '.join(self.valid_reasons)}")
                query = query.filter(FlaggedMessage.reason == reason)

            return query.all()

        except Exception as e:
            logger.error(f"Error retrieving flagged messages: {str(e)}")
            self._get_new_session()
            raise

flagging_service = FlaggingService()
