"""
File utilities for audio file handling and validation.
Supports common audio formats used in meetings.
"""

import os
import tempfile
from typing import BinaryIO, Optional
from fastapi import UploadFile, HTTPException

from src.utils.logger import logger


# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac"
}

# Maximum file size: 25 MB (OpenAI Whisper limit)
MAX_AUDIO_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes


def validate_audio_file(file: UploadFile) -> None:
    """
    Validate uploaded audio file.

    Args:
        file: Uploaded file from FastAPI

    Raises:
        HTTPException: If file is invalid
    """
    # Check if file was provided
    if not file or not file.filename:
        logger.error("audio_validation_failed", reason="No file provided")
        raise HTTPException(status_code=400, detail="No audio file provided")

    # Get file extension
    filename = file.filename.lower()
    file_extension = os.path.splitext(filename)[1]

    # Check if format is supported
    if file_extension not in SUPPORTED_AUDIO_FORMATS:
        supported = ", ".join(SUPPORTED_AUDIO_FORMATS.keys())
        logger.error(
            "audio_validation_failed",
            reason="Unsupported format",
            file_extension=file_extension,
            filename=filename
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{file_extension}'. Supported formats: {supported}"
        )

    # Check file size if available
    if file.size and file.size > MAX_AUDIO_FILE_SIZE:
        size_mb = file.size / (1024 * 1024)
        max_size_mb = MAX_AUDIO_FILE_SIZE / (1024 * 1024)
        logger.error(
            "audio_validation_failed",
            reason="File too large",
            size_mb=size_mb,
            max_size_mb=max_size_mb
        )
        raise HTTPException(
            status_code=400,
            detail=f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
        )

    logger.info(
        "audio_file_validated",
        filename=filename,
        file_extension=file_extension,
        size_bytes=file.size
    )


async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: Optional[str] = None
) -> str:
    """
    Save uploaded file to disk.

    Args:
        upload_file: File uploaded via FastAPI
        destination_dir: Directory to save file (defaults to temp directory)

    Returns:
        Path to saved file

    Raises:
        HTTPException: If save fails
    """
    # Validate file first
    validate_audio_file(upload_file)

    # Determine destination directory
    if destination_dir is None:
        destination_dir = tempfile.gettempdir()

    # Ensure directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Get file extension
    file_extension = os.path.splitext(upload_file.filename)[1]

    # Create temporary file with same extension
    try:
        # Use NamedTemporaryFile to get a unique filename
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=file_extension,
            dir=destination_dir,
            delete=False
        ) as temp_file:
            file_path = temp_file.name

            # Read and write file in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1 MB chunks
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)

        logger.info(
            "audio_file_saved",
            filename=upload_file.filename,
            path=file_path,
            size_bytes=os.path.getsize(file_path)
        )

        return file_path

    except Exception as e:
        logger.error(
            "audio_file_save_failed",
            filename=upload_file.filename,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save audio file: {str(e)}"
        )


def cleanup_file(file_path: str) -> None:
    """
    Delete file from disk.

    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("audio_file_deleted", path=file_path)
    except Exception as e:
        logger.warning(
            "audio_file_cleanup_failed",
            path=file_path,
            error=str(e)
        )


def get_audio_duration_estimate(file_size_bytes: int) -> float:
    """
    Estimate audio duration from file size.

    This is a rough estimate assuming ~128 kbps MP3 encoding.
    For accurate duration, would need to parse audio file headers.

    Args:
        file_size_bytes: File size in bytes

    Returns:
        Estimated duration in seconds
    """
    # Assume 128 kbps encoding = 16 KB/s = 16000 bytes/second
    bytes_per_second = 16000
    estimated_seconds = file_size_bytes / bytes_per_second

    return estimated_seconds


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
