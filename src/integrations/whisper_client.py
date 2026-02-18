"""
OpenAI Whisper API client for audio transcription.
Provides robust audio-to-text conversion with error handling and retries.
"""

import time
from typing import Optional, BinaryIO
from openai import OpenAI, OpenAIError

from src.config import settings
from src.utils.logger import logger


class WhisperClient:
    """
    Client for OpenAI Whisper API transcription.
    Handles audio file transcription with automatic retries and error handling.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whisper client.

        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        """
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.whisper_model

    def transcribe(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> dict:
        """
        Transcribe audio file to text using Whisper API.

        Args:
            audio_file: Audio file object (opened in binary mode)
            language: ISO-639-1 language code (e.g., "en", "es")
            prompt: Optional text to guide transcription style
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Dictionary containing:
                - text: Transcribed text
                - duration: Audio duration in seconds
                - language: Detected language code
                - segments: List of timestamped segments (if available)

        Raises:
            OpenAIError: If transcription fails after all retries
        """
        logger.info(
            "whisper_transcription_started",
            model=self.model,
            language=language,
            temperature=temperature
        )

        start_time = time.time()
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Call Whisper API
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    prompt=prompt,
                    temperature=temperature,
                    response_format="verbose_json"  # Get detailed response with timestamps
                )

                duration = time.time() - start_time

                result = {
                    "text": response.text,
                    "duration": getattr(response, "duration", None),
                    "language": getattr(response, "language", language or "unknown"),
                    "segments": getattr(response, "segments", [])
                }

                logger.info(
                    "whisper_transcription_completed",
                    model=self.model,
                    processing_time_seconds=duration,
                    text_length=len(response.text),
                    word_count=len(response.text.split()),
                    language=result["language"]
                )

                return result

            except OpenAIError as e:
                last_error = e
                logger.warning(
                    "whisper_transcription_retry",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e)
                )

                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(
                        "whisper_retry_wait",
                        wait_seconds=wait_time,
                        next_attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                    # Reset file pointer for retry
                    audio_file.seek(0)
                else:
                    # All retries exhausted
                    logger.error(
                        "whisper_transcription_failed",
                        attempts=max_retries,
                        error=str(e),
                        exc_info=True
                    )
                    raise

        # Should never reach here, but for type safety
        raise last_error or OpenAIError("Transcription failed")

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> dict:
        """
        Convenience method to transcribe from file path.

        Args:
            file_path: Path to audio file
            language: ISO-639-1 language code
            prompt: Optional transcription guide
            temperature: Sampling temperature
            max_retries: Maximum retry attempts

        Returns:
            Transcription result dictionary

        Raises:
            FileNotFoundError: If audio file doesn't exist
            OpenAIError: If transcription fails
        """
        logger.info("whisper_transcribe_file", file_path=file_path)

        with open(file_path, "rb") as audio_file:
            return self.transcribe(
                audio_file=audio_file,
                language=language,
                prompt=prompt,
                temperature=temperature,
                max_retries=max_retries
            )

    def estimate_cost(self, audio_duration_seconds: float) -> float:
        """
        Estimate transcription cost based on audio duration.

        OpenAI Whisper pricing (as of 2026): $0.006 per minute

        Args:
            audio_duration_seconds: Audio duration in seconds

        Returns:
            Estimated cost in USD
        """
        minutes = audio_duration_seconds / 60
        cost_per_minute = 0.006
        return minutes * cost_per_minute

    def health_check(self) -> bool:
        """
        Check if Whisper API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Simple API key validation
            # Note: OpenAI doesn't have a dedicated health endpoint
            # We just verify the client can be initialized
            self.client.models.list()
            logger.info("whisper_health_check_passed")
            return True
        except Exception as e:
            logger.error("whisper_health_check_failed", error=str(e))
            return False
