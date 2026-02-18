"""
Synthesis database model.
Represents the AI-generated synthesis/summary of a conversation.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class Synthesis(BaseModel):
    """
    Conversation synthesis model.

    Stores the AI-generated analysis of a meeting:
    - Key decisions made
    - Action items assigned
    - Open questions
    - Meeting summary
    - Structured data for querying
    """

    __tablename__ = "syntheses"

    # Link to conversation (one-to-one relationship)
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One synthesis per conversation
        index=True
    )

    # Summary
    summary = Column(Text, nullable=False)  # Plain text summary
    summary_word_count = Column(Integer, nullable=True)

    # Structured extraction (JSON fields for flexibility)
    # These are extracted by GPT-4 in structured format
    key_decisions = Column(JSON, nullable=True)  # List of decisions
    action_items = Column(JSON, nullable=True)   # List of action items with owners
    open_questions = Column(JSON, nullable=True) # List of unresolved questions
    key_topics = Column(JSON, nullable=True)     # List of main topics discussed

    # Metadata
    llm_model = Column(String(50), nullable=True)  # gpt-4-turbo-preview, etc.
    llm_tokens_used = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0

    # Email delivery tracking
    email_sent_at = Column(String(255), nullable=True)  # ISO timestamp as string
    email_recipients = Column(JSON, nullable=True)      # List of emails sent to
    email_delivery_status = Column(String(50), nullable=True)  # sent, failed, pending

    # Relationship to conversation
    conversation = relationship(
        "Conversation",
        back_populates="synthesis"
    )

    def __repr__(self) -> str:
        return f"<Synthesis(id={self.id}, conversation_id={self.conversation_id})>"

    @property
    def has_decisions(self) -> bool:
        """Check if any decisions were identified."""
        return bool(self.key_decisions)

    @property
    def has_action_items(self) -> bool:
        """Check if any action items were identified."""
        return bool(self.action_items)

    @property
    def decisions_count(self) -> int:
        """Count of decisions made."""
        return len(self.key_decisions) if self.key_decisions else 0

    @property
    def action_items_count(self) -> int:
        """Count of action items assigned."""
        return len(self.action_items) if self.action_items else 0
