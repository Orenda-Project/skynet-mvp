"""
Conversation repository with specialized query methods.
Extends base repository with conversation-specific operations.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from src.models.conversation import Conversation, ConversationStatus
from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model.
    Provides conversation-specific query methods.
    """

    def __init__(self, db: Session):
        super().__init__(Conversation, db)

    def get_by_status(self, status: ConversationStatus, limit: int = 100) -> List[Conversation]:
        """
        Get conversations by status.

        Args:
            status: Conversation status
            limit: Maximum number of results

        Returns:
            List of conversations with the given status
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.status == status)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_platform_meeting_id(self, platform: str, platform_meeting_id: str) -> Optional[Conversation]:
        """
        Get conversation by platform meeting ID.
        Useful for avoiding duplicate recordings.

        Args:
            platform: Platform name (zoom, teams, etc.)
            platform_meeting_id: Platform-specific meeting ID

        Returns:
            Conversation or None
        """
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.platform == platform,
                Conversation.platform_meeting_id == platform_meeting_id
            )
            .first()
        )

    def get_recent(self, days: int = 7, limit: int = 50) -> List[Conversation]:
        """
        Get recent conversations within the last N days.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent conversations
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        return (
            self.db.query(Conversation)
            .filter(Conversation.created_at >= cutoff)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_with_participants(self, id: str) -> Optional[Conversation]:
        """
        Get conversation with participants eagerly loaded.
        Avoids N+1 query problem.

        Args:
            id: Conversation ID

        Returns:
            Conversation with participants loaded
        """
        return (
            self.db.query(Conversation)
            .options(joinedload(Conversation.participants))
            .filter(Conversation.id == id)
            .first()
        )

    def get_with_synthesis(self, id: str) -> Optional[Conversation]:
        """
        Get conversation with synthesis eagerly loaded.

        Args:
            id: Conversation ID

        Returns:
            Conversation with synthesis loaded
        """
        return (
            self.db.query(Conversation)
            .options(joinedload(Conversation.synthesis))
            .filter(Conversation.id == id)
            .first()
        )

    def get_failed(self, limit: int = 50) -> List[Conversation]:
        """
        Get conversations that failed processing.

        Args:
            limit: Maximum number of results

        Returns:
            List of failed conversations
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.status == ConversationStatus.FAILED)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )

    def search_by_title(self, query: str, limit: int = 20) -> List[Conversation]:
        """
        Search conversations by title.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.title.ilike(f"%{query}%"))
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )
