"""
Pydantic schemas for transcription API.
Follows Guardrail #5: All API inputs/outputs use Pydantic validation.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TranscriptionProvider(str, Enum):
    """Available transcription providers."""
    SONIOX = "soniox"
    WHISPER = "whisper"


class TranscriptionStartRequest(BaseModel):
    """Request to start transcription for uploaded audio."""

    conversation_id: str = Field(
        ...,
        description="ID of conversation to transcribe",
        min_length=1
    )
    language: Optional[str] = Field(
        None,
        description="ISO-639-1 language code (e.g., 'en', 'es')",
        max_length=2
    )
    prefer_provider: Optional[TranscriptionProvider] = Field(
        None,
        description="Preferred transcription provider"
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        """Ensure language code is lowercase if provided."""
        if v:
            return v.lower()
        return v


class AudioUploadRequest(BaseModel):
    """Metadata for audio file upload."""

    title: str = Field(
        ...,
        description="Meeting title",
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        None,
        description="Meeting description",
        max_length=1000
    )
    language: Optional[str] = Field(
        None,
        description="Expected language (e.g., 'en')",
        max_length=2
    )
    platform: Optional[str] = Field(
        None,
        description="Meeting platform (zoom, teams, etc.)",
        max_length=50
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()


class TranscriptionStatusResponse(BaseModel):
    """Response for transcription status check."""

    conversation_id: str = Field(..., description="Conversation ID")
    status: str = Field(..., description="Current status")
    transcript: Optional[str] = Field(None, description="Transcribed text if completed")
    word_count: Optional[int] = Field(None, description="Number of words in transcript")
    provider: Optional[str] = Field(None, description="Provider used for transcription")
    processing_time_seconds: Optional[int] = Field(None, description="Processing time")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "abc123",
                "status": "completed",
                "transcript": "This is the meeting transcript...",
                "word_count": 1250,
                "provider": "whisper",
                "processing_time_seconds": 45,
                "error_message": None
            }
        }


class TranscriptionResult(BaseModel):
    """Detailed transcription result."""

    text: str = Field(..., description="Transcribed text")
    word_count: int = Field(..., description="Number of words")
    provider: str = Field(..., description="Provider used (soniox/whisper)")
    processing_time_seconds: float = Field(..., description="Processing time")
    language: str = Field(..., description="Detected or provided language")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Welcome to the Q1 planning meeting...",
                "word_count": 1250,
                "provider": "whisper",
                "processing_time_seconds": 45.3,
                "language": "en"
            }
        }


class AudioUploadResponse(BaseModel):
    """Response after audio upload."""

    conversation_id: str = Field(..., description="Created conversation ID")
    title: str = Field(..., description="Meeting title")
    status: str = Field(..., description="Current status")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "abc123",
                "title": "Q1 Planning Meeting",
                "status": "pending",
                "message": "Audio uploaded successfully. Use /v1/transcription/start to begin transcription."
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response for transcription providers."""

    whisper: bool = Field(..., description="Whisper API health")
    soniox: bool = Field(..., description="Soniox API health")
    overall: bool = Field(..., description="Overall transcription service health")

    class Config:
        json_schema_extra = {
            "example": {
                "whisper": True,
                "soniox": False,
                "overall": True
            }
        }
