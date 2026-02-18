"""
Synthesis repository with specialized query methods.
Extends base repository with synthesis-specific operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from src.models.synthesis import Synthesis
from src.repositories.base import BaseRepository


class SynthesisRepository(BaseRepository[Synthesis]):
    """
    Repository for Synthesis model.
    Provides synthesis-specific query methods.
    """

    def __init__(self, db: Session):
        super().__init__(Synthesis, db)

    def get_by_conversation_id(self, conversation_id: str) -> Optional[Synthesis]:
        """
        Get synthesis for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Synthesis or None
        """
        return (
            self.db.query(Synthesis)
            .filter(Synthesis.conversation_id == conversation_id)
            .first()
        )

    def get_with_conversation(self, id: str) -> Optional[Synthesis]:
        """
        Get synthesis with conversation eagerly loaded.

        Args:
            id: Synthesis ID

        Returns:
            Synthesis with conversation loaded
        """
        return (
            self.db.query(Synthesis)
            .options(joinedload(Synthesis.conversation))
            .filter(Synthesis.id == id)
            .first()
        )

    def get_with_decisions(self, limit: int = 50) -> List[Synthesis]:
        """
        Get syntheses that contain decisions.

        Args:
            limit: Maximum number of results

        Returns:
            List of syntheses with decisions
        """
        return (
            self.db.query(Synthesis)
            .filter(Synthesis.key_decisions.isnot(None))
            .order_by(Synthesis.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_with_action_items(self, limit: int = 50) -> List[Synthesis]:
        """
        Get syntheses that contain action items.

        Args:
            limit: Maximum number of results

        Returns:
            List of syntheses with action items
        """
        return (
            self.db.query(Synthesis)
            .filter(Synthesis.action_items.isnot(None))
            .order_by(Synthesis.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_email_status(self, status: str, limit: int = 100) -> List[Synthesis]:
        """
        Get syntheses by email delivery status.

        Args:
            status: Email delivery status (sent, failed, pending)
            limit: Maximum number of results

        Returns:
            List of syntheses with the given email status
        """
        return (
            self.db.query(Synthesis)
            .filter(Synthesis.email_delivery_status == status)
            .order_by(Synthesis.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_pending_email(self, limit: int = 100) -> List[Synthesis]:
        """
        Get syntheses pending email delivery.

        Args:
            limit: Maximum number of results

        Returns:
            List of syntheses that need email sent
        """
        return (
            self.db.query(Synthesis)
            .filter(
                (Synthesis.email_delivery_status == "pending") |
                (Synthesis.email_delivery_status.is_(None))
            )
            .order_by(Synthesis.created_at.asc())
            .limit(limit)
            .all()
        )

    def search_summary(self, query: str, limit: int = 20) -> List[Synthesis]:
        """
        Search syntheses by summary content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching syntheses
        """
        return (
            self.db.query(Synthesis)
            .filter(Synthesis.summary.ilike(f"%{query}%"))
            .order_by(Synthesis.created_at.desc())
            .limit(limit)
            .all()
        )
