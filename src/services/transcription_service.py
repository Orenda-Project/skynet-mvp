"""
Transcription service for converting audio to text.
Follows Guardrail #1: Service Layer Isolation - business logic centralized here.
Orchestrates transcription providers with automatic fallback.
"""

import os
import time
from typing import Optional, BinaryIO
from enum import Enum

from src.integrations.whisper_client import WhisperClient
from src.integrations.soniox_client import SonioxClient
from src.repositories.conversation_repository import ConversationRepository
from src.models.conversation import ConversationStatus
from src.utils.logger import logger


class TranscriptionProvider(str, Enum):
    """Available transcription providers."""
    SONIOX = "soniox"
    WHISPER = "whisper"


class TranscriptionService:
    """
    Service for audio transcription with provider fallback.

    Flow:
    1. Try Soniox (if configured)
    2. Fallback to Whisper (if Soniox fails or not configured)
    3. Update conversation with transcript
    4. Track provider and processing time
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        whisper_client: Optional[WhisperClient] = None,
        soniox_client: Optional[SonioxClient] = None
    ):
        """
        Initialize transcription service.

        Args:
            conversation_repo: Repository for conversation persistence
            whisper_client: Whisper API client (injected)
            soniox_client: Soniox API client (injected)
        """
        self.conversation_repo = conversation_repo
        self.whisper_client = whisper_client or WhisperClient()
        self.soniox_client = soniox_client or SonioxClient()

    def transcribe_audio(
        self,
        conversation_id: str,
        audio_file: BinaryIO,
        language: Optional[str] = None,
        prefer_provider: Optional[TranscriptionProvider] = None
    ) -> dict:
        """
        Transcribe audio file and update conversation.

        Args:
            conversation_id: ID of conversation to update
            audio_file: Audio file object (binary mode)
            language: Optional language code (e.g., "en", "es")
            prefer_provider: Preferred provider (defaults to Soniox if available)

        Returns:
            Dictionary containing:
                - text: Transcribed text
                - word_count: Number of words
                - provider: Provider used (soniox/whisper)
                - processing_time_seconds: Time taken
                - language: Detected/provided language

        Raises:
            ValueError: If conversation not found
            Exception: If all providers fail
        """
        logger.info(
            "transcription_started",
            conversation_id=conversation_id,
            language=language,
            prefer_provider=prefer_provider
        )

        # Get conversation
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            logger.error("conversation_not_found", conversation_id=conversation_id)
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update status to TRANSCRIBING
        self.conversation_repo.update(
            conversation_id,
            status=ConversationStatus.TRANSCRIBING
        )

        start_time = time.time()
        transcript_result = None
        provider_used = None
        last_error = None

        # Determine provider order
        providers = self._get_provider_order(prefer_provider)

        # Try each provider in order
        for provider in providers:
            try:
                logger.info(
                    "trying_transcription_provider",
                    provider=provider,
                    conversation_id=conversation_id
                )

                if provider == TranscriptionProvider.SONIOX:
                    if not self.soniox_client.is_available():
                        logger.info(
                            "soniox_skipped",
                            reason="API key not configured"
                        )
                        continue

                    transcript_result = self.soniox_client.transcribe(
                        audio_file=audio_file,
                        language=language
                    )
                    provider_used = TranscriptionProvider.SONIOX

                elif provider == TranscriptionProvider.WHISPER:
                    transcript_result = self.whisper_client.transcribe(
                        audio_file=audio_file,
                        language=language
                    )
                    provider_used = TranscriptionProvider.WHISPER

                # If we got here, transcription succeeded
                break

            except Exception as e:
                last_error = e
                logger.warning(
                    "transcription_provider_failed",
                    provider=provider,
                    error=str(e),
                    conversation_id=conversation_id
                )
                # Reset file pointer for next provider attempt
                audio_file.seek(0)
                continue

        # Check if any provider succeeded
        if transcript_result is None or provider_used is None:
            processing_time = time.time() - start_time
            error_message = f"All transcription providers failed. Last error: {last_error}"

            logger.error(
                "transcription_all_providers_failed",
                conversation_id=conversation_id,
                processing_time_seconds=processing_time,
                last_error=str(last_error)
            )

            # Update conversation with error
            self.conversation_repo.update(
                conversation_id,
                status=ConversationStatus.FAILED,
                error_message=error_message,
                processing_time_seconds=int(processing_time)
            )

            raise Exception(error_message)

        # Success! Process the transcript
        processing_time = time.time() - start_time
        transcript_text = transcript_result["text"]
        word_count = len(transcript_text.split())

        logger.info(
            "transcription_completed",
            conversation_id=conversation_id,
            provider=provider_used,
            word_count=word_count,
            processing_time_seconds=processing_time
        )

        # Update conversation with transcript
        self.conversation_repo.update(
            conversation_id,
            status=ConversationStatus.COMPLETED,  # Will change to SYNTHESIZING later
            transcript=transcript_text,
            transcript_word_count=word_count,
            transcription_provider=provider_used,
            processing_time_seconds=int(processing_time)
        )

        return {
            "text": transcript_text,
            "word_count": word_count,
            "provider": provider_used,
            "processing_time_seconds": processing_time,
            "language": transcript_result.get("language", language or "unknown")
        }

    def transcribe_file(
        self,
        conversation_id: str,
        file_path: str,
        language: Optional[str] = None,
        prefer_provider: Optional[TranscriptionProvider] = None
    ) -> dict:
        """
        Convenience method to transcribe from file path.

        Args:
            conversation_id: Conversation ID
            file_path: Path to audio file
            language: Optional language code
            prefer_provider: Preferred provider

        Returns:
            Transcription result dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If conversation not found
            Exception: If transcription fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        with open(file_path, "rb") as audio_file:
            return self.transcribe_audio(
                conversation_id=conversation_id,
                audio_file=audio_file,
                language=language,
                prefer_provider=prefer_provider
            )

    def _get_provider_order(
        self,
        prefer_provider: Optional[TranscriptionProvider]
    ) -> list[TranscriptionProvider]:
        """
        Determine provider order based on preference and availability.

        Args:
            prefer_provider: Preferred provider

        Returns:
            List of providers in order to try
        """
        if prefer_provider == TranscriptionProvider.WHISPER:
            # User explicitly wants Whisper
            return [TranscriptionProvider.WHISPER]

        if prefer_provider == TranscriptionProvider.SONIOX:
            # User explicitly wants Soniox, fallback to Whisper
            return [TranscriptionProvider.SONIOX, TranscriptionProvider.WHISPER]

        # Default: Try Soniox first if available, then Whisper
        if self.soniox_client.is_available():
            return [TranscriptionProvider.SONIOX, TranscriptionProvider.WHISPER]
        else:
            return [TranscriptionProvider.WHISPER]

    def estimate_cost(
        self,
        audio_duration_seconds: float,
        provider: TranscriptionProvider = TranscriptionProvider.WHISPER
    ) -> float:
        """
        Estimate transcription cost.

        Args:
            audio_duration_seconds: Audio duration in seconds
            provider: Provider to estimate for

        Returns:
            Estimated cost in USD
        """
        if provider == TranscriptionProvider.WHISPER:
            return self.whisper_client.estimate_cost(audio_duration_seconds)
        elif provider == TranscriptionProvider.SONIOX:
            # TODO: Implement when Soniox pricing is known
            return 0.0
        return 0.0

    def health_check(self) -> dict:
        """
        Check health of transcription providers.

        Returns:
            Dictionary with provider health status
        """
        return {
            "whisper": self.whisper_client.health_check(),
            "soniox": self.soniox_client.health_check()
        }
