"""
Pydantic schemas for synthesis API.
Follows Guardrail #5: All API inputs/outputs use Pydantic validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """Action item extracted from meeting."""

    task: str = Field(..., description="What needs to be done")
    owner: Optional[str] = Field(None, description="Who is responsible")
    due_date: Optional[str] = Field(None, description="When it's due")

    class Config:
        json_schema_extra = {
            "example": {
                "task": "Create Q1 product roadmap",
                "owner": "Alice",
                "due_date": "2026-02-01"
            }
        }


class SynthesisGenerateRequest(BaseModel):
    """Request to generate synthesis for a conversation."""

    force_regenerate: bool = Field(
        default=False,
        description="If true, regenerate synthesis even if it already exists"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "force_regenerate": False
            }
        }


class SynthesisResponse(BaseModel):
    """Complete synthesis response with all extracted insights."""

    synthesis_id: str = Field(..., description="Synthesis record ID")
    conversation_id: str = Field(..., description="Associated conversation ID")
    summary: str = Field(..., description="3-sentence meeting summary")
    summary_word_count: Optional[int] = Field(None, description="Word count of summary")
    key_decisions: List[str] = Field(..., description="List of decisions made")
    action_items: List[ActionItem] = Field(..., description="List of action items with owners")
    open_questions: List[str] = Field(..., description="List of unanswered questions")
    key_topics: List[str] = Field(..., description="Main topics discussed")
    llm_model: Optional[str] = Field(None, description="LLM model used for synthesis")
    llm_tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")
    created_at: Optional[str] = Field(None, description="When synthesis was created")
    updated_at: Optional[str] = Field(None, description="When synthesis was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "synthesis_id": "syn-123",
                "conversation_id": "conv-456",
                "summary": "The team discussed Q1 planning priorities. Key decisions included launching the new product feature in February and allocating additional budget for marketing. Several action items were assigned with clear ownership.",
                "summary_word_count": 34,
                "key_decisions": [
                    "Launch new product feature in February 2026",
                    "Allocate $50k additional budget for marketing campaign",
                    "Hire 2 additional engineers for backend team"
                ],
                "action_items": [
                    {
                        "task": "Create detailed product launch timeline",
                        "owner": "Alice",
                        "due_date": "2026-02-01"
                    },
                    {
                        "task": "Draft marketing campaign proposal",
                        "owner": "Bob",
                        "due_date": "2026-01-30"
                    }
                ],
                "open_questions": [
                    "What pricing model should we use for the new feature?",
                    "Do we need to hire contractors or full-time employees?"
                ],
                "key_topics": [
                    "Product Launch Planning",
                    "Budget Allocation",
                    "Team Expansion",
                    "Marketing Strategy"
                ],
                "llm_model": "gpt-4-turbo-preview",
                "llm_tokens_used": 2500,
                "processing_time_seconds": 8.5,
                "created_at": "2026-01-23T10:30:00",
                "updated_at": "2026-01-23T10:30:00"
            }
        }


class SynthesisGenerateResponse(BaseModel):
    """Response after generating synthesis (subset of full synthesis)."""

    synthesis_id: str = Field(..., description="Synthesis record ID")
    summary: str = Field(..., description="Meeting summary")
    key_decisions: List[str] = Field(..., description="Decisions made")
    action_items: List[ActionItem] = Field(..., description="Action items")
    open_questions: List[str] = Field(..., description="Unanswered questions")
    key_topics: List[str] = Field(..., description="Main topics")
    llm_model: str = Field(..., description="LLM model used")
    llm_tokens_used: int = Field(..., description="Tokens consumed")
    processing_time_seconds: float = Field(..., description="Processing time")

    class Config:
        json_schema_extra = {
            "example": {
                "synthesis_id": "syn-123",
                "summary": "The team discussed Q1 planning priorities...",
                "key_decisions": [
                    "Launch new product feature in February 2026"
                ],
                "action_items": [
                    {
                        "task": "Create product launch timeline",
                        "owner": "Alice",
                        "due_date": "2026-02-01"
                    }
                ],
                "open_questions": [
                    "What pricing model should we use?"
                ],
                "key_topics": [
                    "Product Launch Planning",
                    "Budget Allocation"
                ],
                "llm_model": "gpt-4-turbo-preview",
                "llm_tokens_used": 2500,
                "processing_time_seconds": 8.5
            }
        }


class CostEstimateResponse(BaseModel):
    """Cost estimate for synthesis generation."""

    conversation_id: str = Field(..., description="Conversation ID")
    transcript_word_count: int = Field(..., description="Number of words in transcript")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    model: str = Field(..., description="Model used for estimation")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-456",
                "transcript_word_count": 3500,
                "estimated_cost_usd": 0.045,
                "model": "gpt-4-turbo-preview"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response for synthesis service."""

    openai_gpt4: bool = Field(..., description="OpenAI GPT-4 API health")
    overall: bool = Field(..., description="Overall synthesis service health")

    class Config:
        json_schema_extra = {
            "example": {
                "openai_gpt4": True,
                "overall": True
            }
        }
