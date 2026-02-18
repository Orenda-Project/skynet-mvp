"""
Transcription API endpoints (v1).
Follows Guardrail #1: Routes are thin adapters, delegate to services.
Follows Guardrail #10: All routes have /v1/ prefix for versioning.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from src.database.postgres import get_db
from src.repositories.conversation_repository import ConversationRepository
from src.services.transcription_service import TranscriptionService, TranscriptionProvider
from src.schemas.transcription import (
    AudioUploadResponse,
    TranscriptionStatusResponse,
    TranscriptionResult,
    HealthCheckResponse
)
from src.models.conversation import ConversationStatus
from src.utils.file_utils import save_upload_file, cleanup_file
from src.utils.logger import logger

router = APIRouter(prefix="/v1/transcription", tags=["transcription"])


def get_transcription_service(db: Session = Depends(get_db)) -> TranscriptionService:
    """
    Dependency injection for transcription service.

    Args:
        db: Database session

    Returns:
        TranscriptionService instance
    """
    conversation_repo = ConversationRepository(db)
    return TranscriptionService(conversation_repo=conversation_repo)


@router.post("/upload", response_model=AudioUploadResponse, status_code=201)
async def upload_audio(
    title: str = Form(..., description="Meeting title"),
    description: str = Form(None, description="Meeting description"),
    language: str = Form(None, description="Expected language (e.g., 'en')"),
    platform: str = Form(None, description="Meeting platform (zoom, teams, etc.)"),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Create conversation record for transcription.

    This endpoint:
    1. Creates conversation in database
    2. Returns conversation ID

    Use `/v1/transcription/transcribe/{conversation_id}` with audio file to transcribe.
    """
    logger.info(
        "conversation_create_request",
        title=title,
        language=language
    )

    # Create conversation record
    conversation = transcription_service.conversation_repo.create(
        title=title.strip(),
        description=description.strip() if description else None,
        status=ConversationStatus.PENDING,
        platform=platform
    )

    logger.info(
        "conversation_created",
        conversation_id=conversation.id,
        title=title
    )

    return AudioUploadResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        status=conversation.status.value,
        message="Conversation created. Upload your audio file via /v1/transcription/transcribe"
    )


@router.post("/transcribe/{conversation_id}", response_model=TranscriptionResult)
async def transcribe_audio(
    conversation_id: str,
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(None, description="Language code (e.g., 'en')"),
    prefer_provider: str = Form(None, description="Preferred provider (whisper/soniox)"),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Transcribe audio file for a conversation.

    This endpoint:
    1. Validates and saves audio file
    2. Transcribes using Whisper (or Soniox if configured)
    3. Updates conversation with transcript
    4. Returns transcription result

    Audio file is automatically deleted after processing.
    """
    logger.info(
        "transcribe_request",
        conversation_id=conversation_id,
        filename=file.filename,
        language=language,
        prefer_provider=prefer_provider
    )

    # Save uploaded file
    file_path = None
    try:
        file_path = await save_upload_file(file)

        # Parse provider preference
        provider_enum = None
        if prefer_provider:
            try:
                provider_enum = TranscriptionProvider(prefer_provider.lower())
            except ValueError:
                logger.warning(
                    "invalid_provider_preference",
                    prefer_provider=prefer_provider
                )

        # Transcribe file
        result = transcription_service.transcribe_file(
            conversation_id=conversation_id,
            file_path=file_path,
            language=language,
            prefer_provider=provider_enum
        )

        logger.info(
            "transcribe_completed",
            conversation_id=conversation_id,
            word_count=result["word_count"],
            provider=result["provider"]
        )

        return TranscriptionResult(**result)

    except ValueError as e:
        # Conversation not found
        logger.error("transcribe_failed", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # Transcription failed
        logger.error(
            "transcribe_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    finally:
        # Cleanup uploaded file
        if file_path:
            cleanup_file(file_path)


@router.get("/status/{conversation_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(
    conversation_id: str,
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Check transcription status for a conversation.

    Returns:
    - Current status (pending/transcribing/completed/failed)
    - Transcript if completed
    - Error message if failed
    """
    conversation = transcription_service.conversation_repo.get_by_id(conversation_id)

    if not conversation:
        logger.error("conversation_not_found", conversation_id=conversation_id)
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return TranscriptionStatusResponse(
        conversation_id=conversation.id,
        status=conversation.status.value,
        transcript=conversation.transcript,
        word_count=conversation.transcript_word_count,
        provider=conversation.transcription_provider,
        processing_time_seconds=conversation.processing_time_seconds,
        error_message=conversation.error_message
    )


@router.get("/health", response_model=HealthCheckResponse)
async def transcription_health_check(
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Health check for transcription providers.

    Returns availability status for:
    - Whisper API
    - Soniox API (if configured)
    - Overall transcription service
    """
    health = transcription_service.health_check()

    # Overall health is true if at least one provider is healthy
    overall = health["whisper"] or health["soniox"]

    return HealthCheckResponse(
        whisper=health["whisper"],
        soniox=health["soniox"],
        overall=overall
    )
