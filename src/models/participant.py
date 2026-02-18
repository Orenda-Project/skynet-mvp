"""
Participant database model.
Represents a person who participated in a conversation/meeting.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Participant(BaseModel):
    """
    Meeting participant model.

    Stores information about who attended a meeting:
    - Name and email
    - Whether they were the organizer
    - Link back to the conversation
    """

    __tablename__ = "participants"

    # Participant identity
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)

    # Role in meeting
    is_organizer = Column(Boolean, default=False, nullable=False)

    # Link to conversation
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationship to conversation
    conversation = relationship(
        "Conversation",
        back_populates="participants"
    )

    def __repr__(self) -> str:
        return f"<Participant(id={self.id}, name={self.name}, email={self.email})>"

    @property
    def display_name(self) -> str:
        """Get formatted display name with email."""
        return f"{self.name} <{self.email}>"
