"""
Email service for sending synthesis emails to participants.
Follows Guardrail #1: Service Layer Isolation - business logic centralized here.
"""

import os
from datetime import datetime
from typing import Optional, List
from jinja2 import Template

from src.integrations.smtp_client import SMTPClient
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.synthesis_repository import SynthesisRepository
from src.utils.logger import logger


class EmailService:
    """
    Service for sending synthesis emails to meeting participants.

    Flow:
    1. Get conversation and synthesis
    2. Get participants from conversation
    3. Render HTML email template
    4. Send email to all participants
    5. Update synthesis with delivery status
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        synthesis_repo: SynthesisRepository,
        smtp_client: Optional[SMTPClient] = None
    ):
        """
        Initialize email service.

        Args:
            conversation_repo: Repository for conversation data
            synthesis_repo: Repository for synthesis data
            smtp_client: SMTP client for sending emails (injected)
        """
        self.conversation_repo = conversation_repo
        self.synthesis_repo = synthesis_repo
        self.smtp_client = smtp_client or SMTPClient()

        # Load email template
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates',
            'synthesis_email.html'
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            self.email_template = Template(f.read())

    def send_synthesis_email(
        self,
        conversation_id: str,
        custom_recipients: Optional[List[str]] = None
    ) -> dict:
        """
        Send synthesis email to meeting participants.

        Args:
            conversation_id: ID of conversation to send synthesis for
            custom_recipients: Optional list of custom recipients (overrides participants)

        Returns:
            Dictionary containing:
                - success: True if sent successfully
                - message: Success/error message
                - recipients: List of recipients
                - sent_at: Timestamp when sent

        Raises:
            ValueError: If conversation/synthesis not found or no participants
            Exception: If email sending fails
        """
        logger.info(
            "synthesis_email_send_started",
            conversation_id=conversation_id,
            custom_recipients=custom_recipients
        )

        # Get conversation
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            logger.error("conversation_not_found", conversation_id=conversation_id)
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get synthesis
        synthesis = self.synthesis_repo.get_by_conversation_id(conversation_id)
        if not synthesis:
            logger.error(
                "synthesis_not_found",
                conversation_id=conversation_id
            )
            raise ValueError(
                f"No synthesis found for conversation {conversation_id}. "
                f"Generate synthesis first using POST /v1/synthesis/generate"
            )

        # Get recipients
        if custom_recipients:
            recipients = custom_recipients
            logger.info(
                "using_custom_recipients",
                conversation_id=conversation_id,
                recipients=recipients
            )
        else:
            # Get participants from conversation
            conversation_with_participants = self.conversation_repo.get_with_participants(
                conversation_id
            )
            if not conversation_with_participants or not conversation_with_participants.participants:
                logger.error(
                    "no_participants_found",
                    conversation_id=conversation_id
                )
                raise ValueError(
                    f"No participants found for conversation {conversation_id}. "
                    f"Add participants or specify custom_recipients."
                )

            recipients = [p.email for p in conversation_with_participants.participants if p.email]

            if not recipients:
                raise ValueError("No valid email addresses found in participants")

            logger.info(
                "sending_to_participants",
                conversation_id=conversation_id,
                recipient_count=len(recipients),
                recipients=recipients
            )

        # Render email HTML
        html_body = self._render_email_html(
            title=conversation.title,
            date=conversation.created_at.strftime("%B %d, %Y at %I:%M %p"),
            summary=synthesis.summary,
            decisions=synthesis.key_decisions or [],
            action_items=synthesis.action_items or [],
            open_questions=synthesis.open_questions or [],
            topics=synthesis.key_topics or []
        )

        # Generate plain text fallback
        text_body = self._generate_text_body(
            title=conversation.title,
            summary=synthesis.summary,
            decisions=synthesis.key_decisions or [],
            action_items=synthesis.action_items or [],
            open_questions=synthesis.open_questions or [],
            topics=synthesis.key_topics or []
        )

        # Send email
        try:
            result = self.smtp_client.send_email(
                to_emails=recipients,
                subject=f"Meeting Synthesis: {conversation.title}",
                html_body=html_body,
                text_body=text_body
            )

            # Update synthesis with email delivery status
            self.synthesis_repo.update(
                synthesis.id,
                email_sent_at=datetime.utcnow().isoformat(),
                email_recipients=recipients,
                email_delivery_status="sent"
            )

            logger.info(
                "synthesis_email_sent_successfully",
                conversation_id=conversation_id,
                synthesis_id=synthesis.id,
                recipients=recipients
            )

            return {
                "success": True,
                "message": f"Synthesis email sent to {len(recipients)} recipient(s)",
                "recipients": recipients,
                "sent_at": result["sent_at"]
            }

        except Exception as e:
            # Update synthesis with failure status
            self.synthesis_repo.update(
                synthesis.id,
                email_delivery_status="failed"
            )

            logger.error(
                "synthesis_email_send_failed",
                conversation_id=conversation_id,
                synthesis_id=synthesis.id,
                error=str(e),
                exc_info=True
            )

            raise

    def preview_email(self, conversation_id: str) -> str:
        """
        Generate HTML preview of synthesis email.

        Args:
            conversation_id: ID of conversation

        Returns:
            HTML email preview

        Raises:
            ValueError: If conversation/synthesis not found
        """
        # Get conversation
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get synthesis
        synthesis = self.synthesis_repo.get_by_conversation_id(conversation_id)
        if not synthesis:
            raise ValueError(f"No synthesis found for conversation {conversation_id}")

        # Render email HTML
        html_body = self._render_email_html(
            title=conversation.title,
            date=conversation.created_at.strftime("%B %d, %Y at %I:%M %p"),
            summary=synthesis.summary,
            decisions=synthesis.key_decisions or [],
            action_items=synthesis.action_items or [],
            open_questions=synthesis.open_questions or [],
            topics=synthesis.key_topics or []
        )

        return html_body

    def _render_email_html(
        self,
        title: str,
        date: str,
        summary: str,
        decisions: List[str],
        action_items: List[dict],
        open_questions: List[str],
        topics: List[str]
    ) -> str:
        """
        Render email HTML from template.

        Args:
            title: Meeting title
            date: Meeting date formatted string
            summary: Summary text
            decisions: List of decisions
            action_items: List of action item dicts
            open_questions: List of questions
            topics: List of topics

        Returns:
            Rendered HTML string
        """
        return self.email_template.render(
            title=title,
            date=date,
            summary=summary,
            decisions=decisions,
            action_items=action_items,
            open_questions=open_questions,
            topics=topics
        )

    def _generate_text_body(
        self,
        title: str,
        summary: str,
        decisions: List[str],
        action_items: List[dict],
        open_questions: List[str],
        topics: List[str]
    ) -> str:
        """
        Generate plain text email body.

        Args:
            title: Meeting title
            summary: Summary text
            decisions: List of decisions
            action_items: List of action item dicts
            open_questions: List of questions
            topics: List of topics

        Returns:
            Plain text email body
        """
        lines = [
            f"MEETING SYNTHESIS: {title}",
            "=" * 60,
            "",
            "SUMMARY",
            "-" * 60,
            summary,
            ""
        ]

        if decisions:
            lines.extend([
                "",
                f"KEY DECISIONS ({len(decisions)})",
                "-" * 60
            ])
            for i, decision in enumerate(decisions, 1):
                lines.append(f"{i}. {decision}")

        if action_items:
            lines.extend([
                "",
                f"ACTION ITEMS ({len(action_items)})",
                "-" * 60
            ])
            for i, item in enumerate(action_items, 1):
                lines.append(f"{i}. {item['task']}")
                if item.get('owner'):
                    lines.append(f"   Owner: {item['owner']}")
                if item.get('due_date'):
                    lines.append(f"   Due: {item['due_date']}")

        if open_questions:
            lines.extend([
                "",
                f"OPEN QUESTIONS ({len(open_questions)})",
                "-" * 60
            ])
            for i, question in enumerate(open_questions, 1):
                lines.append(f"{i}. {question}")

        if topics:
            lines.extend([
                "",
                "KEY TOPICS",
                "-" * 60,
                ", ".join(topics)
            ])

        lines.extend([
            "",
            "=" * 60,
            "Generated by SkyNet - Organizational Intelligence System"
        ])

        return "\n".join(lines)

    def health_check(self) -> bool:
        """
        Check health of email service.

        Returns:
            True if SMTP connection healthy, False otherwise
        """
        return self.smtp_client.health_check()
