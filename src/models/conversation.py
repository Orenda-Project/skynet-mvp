"""
Conversation (Meeting) database model.
Represents a single meeting/conversation that was recorded and processed.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel


class ConversationStatus(str, enum.Enum):
    """Status of a conversation in the processing pipeline."""
    PENDING = "pending"           # Created but not yet processed
    TRANSCRIBING = "transcribing" # Audio being transcribed
    SYNTHESIZING = "synthesizing" # Transcript being analyzed
    COMPLETED = "completed"       # Fully processed, synthesis sent
    FAILED = "failed"            # Processing failed


class Conversation(BaseModel):
    """
    Meeting/Conversation model.

    Stores information about a meeting:
    - When it happened
    - Who participated
    - How long it lasted
    - Processing status
    - Link to the transcript and synthesis
    """

    __tablename__ = "conversations"

    # Meeting metadata
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Timing
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Calculated duration

    # Processing status
    status = Column(
        SQLEnum(ConversationStatus),
        default=ConversationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Meeting platform info (optional)
    platform = Column(String(50), nullable=True)  # zoom, teams, meet, etc.
    platform_meeting_id = Column(String(255), nullable=True, index=True)
    meeting_url = Column(String(512), nullable=True)

    # Transcript (stored as text for now, could move to separate table if needed)
    transcript = Column(Text, nullable=True)
    transcript_word_count = Column(Integer, nullable=True)

    # Processing metadata
    transcription_provider = Column(String(50), nullable=True)  # soniox, whisper
    synthesis_provider = Column(String(50), nullable=True)     # gpt-4, claude
    processing_time_seconds = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Relationships
    participants = relationship(
        "Participant",
        back_populates="conversation",
        cascade="all, delete-orphan"  # Delete participants when conversation is deleted
    )
    synthesis = relationship(
        "Synthesis",
        back_populates="conversation",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Check if conversation processing is complete."""
        return self.status == ConversationStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if conversation processing failed."""
        return self.status == ConversationStatus.FAILED

    @property
    def duration_minutes(self) -> float | None:
        """Get duration in minutes (more readable than seconds)."""
        return self.duration_seconds / 60.0 if self.duration_seconds else None
