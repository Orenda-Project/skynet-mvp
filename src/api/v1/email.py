"""
Email API endpoints (v1).
Follows Guardrail #1: Routes are thin adapters, delegate to services.
Follows Guardrail #10: All routes have /v1/ prefix for versioning.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.database.postgres import get_db
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.synthesis_repository import SynthesisRepository
from src.services.email_service import EmailService
from src.schemas.email import (
    EmailSendRequest,
    EmailSendResponse,
    EmailPreviewResponse,
    EmailHealthCheckResponse
)
from src.utils.logger import logger

router = APIRouter(prefix="/v1/email", tags=["email"])


def get_email_service(db: Session = Depends(get_db)) -> EmailService:
    """
    Dependency injection for email service.

    Args:
        db: Database session

    Returns:
        EmailService instance
    """
    conversation_repo = ConversationRepository(db)
    synthesis_repo = SynthesisRepository(db)
    return EmailService(
        conversation_repo=conversation_repo,
        synthesis_repo=synthesis_repo
    )


@router.post("/send/{conversation_id}", response_model=EmailSendResponse)
async def send_synthesis_email(
    conversation_id: str,
    request: EmailSendRequest = Body(default=EmailSendRequest()),
    email_service: EmailService = Depends(get_email_service)
):
    """
    Send synthesis email to meeting participants.

    This endpoint:
    1. Gets conversation and synthesis from database
    2. Retrieves participant email addresses (or uses custom_recipients)
    3. Renders beautiful HTML email with synthesis
    4. Sends email via SMTP
    5. Updates synthesis with delivery status

    **Note**: Synthesis must exist before sending email (generate it first).
    """
    logger.info(
        "email_send_request",
        conversation_id=conversation_id,
        custom_recipients=request.custom_recipients
    )

    try:
        result = email_service.send_synthesis_email(
            conversation_id=conversation_id,
            custom_recipients=request.custom_recipients
        )

        logger.info(
            "email_send_success",
            conversation_id=conversation_id,
            recipient_count=len(result["recipients"])
        )

        return EmailSendResponse(**result)

    except ValueError as e:
        # Conversation/synthesis not found or no participants
        logger.error(
            "email_send_failed",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Email sending failed
        logger.error(
            "email_send_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


@router.get("/preview/{conversation_id}", response_class=HTMLResponse)
async def preview_synthesis_email(
    conversation_id: str,
    email_service: EmailService = Depends(get_email_service)
):
    """
    Preview synthesis email HTML.

    Returns the rendered HTML email for preview purposes.
    Useful for testing email template before sending.

    **Note**: Synthesis must exist to preview email.
    """
    try:
        html = email_service.preview_email(conversation_id)
        return HTMLResponse(content=html)

    except ValueError as e:
        # Conversation/synthesis not found
        logger.error(
            "email_preview_failed",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # Preview generation failed
        logger.error(
            "email_preview_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/health", response_model=EmailHealthCheckResponse)
async def email_health_check(
    email_service: EmailService = Depends(get_email_service)
):
    """
    Health check for email service.

    Returns availability status for:
    - SMTP connection
    - Overall email service

    **Useful for**: Monitoring and pre-flight checks before sending emails.
    """
    health = email_service.health_check()

    return EmailHealthCheckResponse(
        smtp_connection=health,
        overall=health
    )
