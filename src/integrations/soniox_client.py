"""
Soniox API client for audio transcription.
Placeholder implementation - activate when SONIOX_API_KEY is available.
"""

from typing import Optional, BinaryIO

from src.config import settings
from src.utils.logger import logger


class SonioxClient:
    """
    Client for Soniox API transcription.

    Note: This is currently a stub implementation.
    To activate:
    1. Set SONIOX_API_KEY in .env
    2. Install soniox SDK: pip install soniox
    3. Uncomment the implementation below
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Soniox client.

        Args:
            api_key: Soniox API key (defaults to settings.soniox_api_key)
        """
        self.api_key = api_key or getattr(settings, "soniox_api_key", None)

        if not self.api_key:
            logger.info(
                "soniox_client_disabled",
                message="SONIOX_API_KEY not set, client will not be available"
            )

    def is_available(self) -> bool:
        """
        Check if Soniox is configured and available.

        Returns:
            True if API key is set, False otherwise
        """
        return self.api_key is not None and self.api_key != ""

    def transcribe(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False,
        max_retries: int = 3
    ) -> dict:
        """
        Transcribe audio file using Soniox API.

        Args:
            audio_file: Audio file object
            language: Language code
            enable_speaker_diarization: Enable speaker identification
            max_retries: Maximum retry attempts

        Returns:
            Dictionary containing:
                - text: Transcribed text
                - duration: Audio duration
                - language: Detected language
                - speakers: Speaker diarization data (if enabled)

        Raises:
            NotImplementedError: Soniox not yet configured
        """
        if not self.is_available():
            logger.error(
                "soniox_not_configured",
                message="SONIOX_API_KEY not set. Set it in .env to enable Soniox."
            )
            raise NotImplementedError(
                "Soniox transcription requires SONIOX_API_KEY. "
                "Please set it in your .env file."
            )

        # TODO: Implement when Soniox API key is available
        # Example implementation:
        """
        from soniox import SonioxClient as SonioxSDK

        client = SonioxSDK(api_key=self.api_key)

        response = client.transcribe(
            audio=audio_file,
            language=language,
            enable_speaker_diarization=enable_speaker_diarization
        )

        return {
            "text": response.text,
            "duration": response.duration,
            "language": response.language,
            "speakers": response.speakers if enable_speaker_diarization else None
        }
        """

        raise NotImplementedError("Soniox integration pending API key")

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False,
        max_retries: int = 3
    ) -> dict:
        """
        Transcribe from file path.

        Args:
            file_path: Path to audio file
            language: Language code
            enable_speaker_diarization: Enable speaker identification
            max_retries: Maximum retry attempts

        Returns:
            Transcription result

        Raises:
            NotImplementedError: Soniox not configured
        """
        with open(file_path, "rb") as audio_file:
            return self.transcribe(
                audio_file=audio_file,
                language=language,
                enable_speaker_diarization=enable_speaker_diarization,
                max_retries=max_retries
            )

    def health_check(self) -> bool:
        """
        Check if Soniox API is accessible.

        Returns:
            True if available and healthy, False otherwise
        """
        if not self.is_available():
            logger.info("soniox_health_check_skipped", reason="API key not configured")
            return False

        # TODO: Implement actual health check when SDK available
        logger.warning("soniox_health_check_not_implemented")
        return False


# Instructions for activating Soniox:
"""
1. Get Soniox API key from https://soniox.com

2. Add to .env:
   SONIOX_API_KEY=your_soniox_api_key_here

3. Add to src/config.py Settings class:
   soniox_api_key: Optional[str] = None

4. Install Soniox SDK:
   pip install soniox

5. Replace the stub implementation above with actual Soniox API calls

6. Update transcription_service.py to prefer Soniox over Whisper
"""
