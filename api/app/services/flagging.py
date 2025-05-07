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
        """
        Flag a message for moderation.
        
        Args:
            message_id: UUID of the message to flag
            reason: One of 'hallucination', 'inappropriate', 'inaccurate', 'other'
            wallet_address: Address of the user flagging the message
            note: Optional note explaining the flag
            
        Returns:
            FlaggedMessage object
            
        Raises:
            ValueError: If reason is invalid or message not found
            Exception: For database errors
        """
        try:
            # Validate reason
            if reason not in self.valid_reasons:
                raise ValueError(f"Invalid reason. Must be one of: {', '.join(self.valid_reasons)}")

            # Convert message_id to UUID
            try:
                message_uuid = uuid.UUID(message_id)
            except ValueError:
                raise ValueError(f"Invalid message ID format: {message_id}")

            # Check if message exists
            message = self.db.query(ChatMessageDB).filter(ChatMessageDB.id == message_uuid).first()
            if not message:
                raise ValueError(f"Message with ID {message_id} not found")

            # Create flagged message record
            flagged_message = FlaggedMessage(
                message_id=message_uuid,
                reason=reason,
                note=note,
                wallet_address=wallet_address.lower()  # Standardize wallet address
            )

            self.db.add(flagged_message)
            self.db.commit()
            self.db.refresh(flagged_message)

            logger.info(f"Message {message_id} flagged by {wallet_address} for reason: {reason}")
            return flagged_message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error flagging message: {str(e)}")
            self._get_new_session()
            raise

    def get_flagged_messages(
        self,
        wallet_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> List[FlaggedMessage]:
        """
        Get flagged messages with optional filtering.
        
        Args:
            wallet_address: Optional filter by flagger's wallet address
            reason: Optional filter by flag reason
            
        Returns:
            List of FlaggedMessage objects
        """
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
