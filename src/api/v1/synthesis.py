"""
Synthesis API endpoints (v1).
Follows Guardrail #1: Routes are thin adapters, delegate to services.
Follows Guardrail #10: All routes have /v1/ prefix for versioning.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from src.database.postgres import get_db
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.synthesis_repository import SynthesisRepository
from src.services.synthesis_service import SynthesisService
from src.schemas.synthesis import (
    SynthesisGenerateRequest,
    SynthesisGenerateResponse,
    SynthesisResponse,
    CostEstimateResponse,
    HealthCheckResponse,
    ActionItem
)
from src.utils.logger import logger

router = APIRouter(prefix="/v1/synthesis", tags=["synthesis"])


def get_synthesis_service(db: Session = Depends(get_db)) -> SynthesisService:
    """
    Dependency injection for synthesis service.

    Args:
        db: Database session

    Returns:
        SynthesisService instance
    """
    conversation_repo = ConversationRepository(db)
    synthesis_repo = SynthesisRepository(db)
    return SynthesisService(
        conversation_repo=conversation_repo,
        synthesis_repo=synthesis_repo
    )


@router.post("/generate/{conversation_id}", response_model=SynthesisGenerateResponse)
async def generate_synthesis(
    conversation_id: str,
    request: SynthesisGenerateRequest = Body(default=SynthesisGenerateRequest()),
    synthesis_service: SynthesisService = Depends(get_synthesis_service)
):
    """
    Generate synthesis for a conversation's transcript.

    This endpoint:
    1. Validates conversation exists and has transcript
    2. Calls GPT-4 to extract insights (summary, decisions, action items, questions)
    3. Stores synthesis in database
    4. Returns structured synthesis

    **Note**: If synthesis already exists, returns existing unless force_regenerate=true
    """
    logger.info(
        "synthesis_generate_request",
        conversation_id=conversation_id,
        force_regenerate=request.force_regenerate
    )

    try:
        result = synthesis_service.generate_synthesis(
            conversation_id=conversation_id,
            force_regenerate=request.force_regenerate
        )

        logger.info(
            "synthesis_generate_success",
            conversation_id=conversation_id,
            synthesis_id=result["synthesis_id"]
        )

        # Convert action_items to ActionItem objects
        action_items = [ActionItem(**item) for item in result["action_items"]]

        return SynthesisGenerateResponse(
            synthesis_id=result["synthesis_id"],
            summary=result["summary"],
            key_decisions=result["key_decisions"],
            action_items=action_items,
            open_questions=result["open_questions"],
            key_topics=result["key_topics"],
            llm_model=result["llm_model"],
            llm_tokens_used=result["llm_tokens_used"],
            processing_time_seconds=result["processing_time_seconds"]
        )

    except ValueError as e:
        # Conversation not found or no transcript
        logger.error(
            "synthesis_generate_failed",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Synthesis generation failed
        logger.error(
            "synthesis_generate_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis generation failed: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=SynthesisResponse)
async def get_synthesis(
    conversation_id: str,
    synthesis_service: SynthesisService = Depends(get_synthesis_service)
):
    """
    Get existing synthesis for a conversation.

    Returns the complete synthesis if it exists, including all extracted insights.

    **Note**: This does NOT generate synthesis - use POST /generate first.
    """
    synthesis = synthesis_service.get_synthesis(conversation_id)

    if not synthesis:
        logger.error(
            "synthesis_not_found",
            conversation_id=conversation_id
        )
        raise HTTPException(
            status_code=404,
            detail=f"No synthesis found for conversation {conversation_id}. "
                   f"Use POST /v1/synthesis/generate/{conversation_id} to create one."
        )

    # Convert action_items to ActionItem objects
    action_items = [ActionItem(**item) for item in synthesis["action_items"]]

    return SynthesisResponse(
        synthesis_id=synthesis["synthesis_id"],
        conversation_id=synthesis["conversation_id"],
        summary=synthesis["summary"],
        summary_word_count=synthesis["summary_word_count"],
        key_decisions=synthesis["key_decisions"],
        action_items=action_items,
        open_questions=synthesis["open_questions"],
        key_topics=synthesis["key_topics"],
        llm_model=synthesis["llm_model"],
        llm_tokens_used=synthesis["llm_tokens_used"],
        processing_time_seconds=synthesis["processing_time_seconds"],
        created_at=synthesis["created_at"],
        updated_at=synthesis["updated_at"]
    )


@router.get("/cost-estimate/{conversation_id}", response_model=CostEstimateResponse)
async def estimate_synthesis_cost(
    conversation_id: str,
    synthesis_service: SynthesisService = Depends(get_synthesis_service)
):
    """
    Estimate cost for generating synthesis.

    Returns estimated cost in USD based on transcript length and GPT-4 pricing.

    **Useful for**: Checking cost before generating synthesis for long meetings.
    """
    try:
        # Get conversation to get word count
        conversation = synthesis_service.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )

        estimated_cost = synthesis_service.estimate_cost(conversation_id)

        return CostEstimateResponse(
            conversation_id=conversation_id,
            transcript_word_count=conversation.transcript_word_count or 0,
            estimated_cost_usd=estimated_cost,
            model=synthesis_service.synthesis_client.model
        )

    except ValueError as e:
        logger.error(
            "cost_estimate_failed",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "cost_estimate_failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Cost estimation failed: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def synthesis_health_check(
    synthesis_service: SynthesisService = Depends(get_synthesis_service)
):
    """
    Health check for synthesis service.

    Returns availability status for:
    - OpenAI GPT-4 API
    - Overall synthesis service

    **Useful for**: Monitoring and pre-flight checks.
    """
    health = synthesis_service.health_check()

    return HealthCheckResponse(
        openai_gpt4=health,
        overall=health
    )
