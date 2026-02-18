"""
Pydantic schemas for email API.
Follows Guardrail #5: All API inputs/outputs use Pydantic validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class EmailSendRequest(BaseModel):
    """Request to send synthesis email."""

    custom_recipients: Optional[List[EmailStr]] = Field(
        None,
        description="Optional list of custom recipients (overrides participants)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "custom_recipients": ["alice@example.com", "bob@example.com"]
            }
        }


class EmailSendResponse(BaseModel):
    """Response after sending email."""

    success: bool = Field(..., description="Whether email was sent successfully")
    message: str = Field(..., description="Success/error message")
    recipients: List[str] = Field(..., description="List of recipients")
    sent_at: float = Field(..., description="Timestamp when sent")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Synthesis email sent to 3 recipient(s)",
                "recipients": ["alice@example.com", "bob@example.com", "charlie@example.com"],
                "sent_at": 1706284800.0
            }
        }


class EmailPreviewResponse(BaseModel):
    """Response with email HTML preview."""

    html: str = Field(..., description="HTML email preview")
    subject: str = Field(..., description="Email subject line")

    class Config:
        json_schema_extra = {
            "example": {
                "html": "<html>...</html>",
                "subject": "Meeting Synthesis: Q1 Planning Meeting"
            }
        }


class EmailHealthCheckResponse(BaseModel):
    """Health check response for email service."""

    smtp_connection: bool = Field(..., description="SMTP connection health")
    overall: bool = Field(..., description="Overall email service health")

    class Config:
        json_schema_extra = {
            "example": {
                "smtp_connection": True,
                "overall": True
            }
        }
