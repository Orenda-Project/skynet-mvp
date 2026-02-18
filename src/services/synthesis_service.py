"""
Synthesis service for generating meeting insights from transcripts.
Follows Guardrail #1: Service Layer Isolation - business logic centralized here.
Orchestrates GPT-4 synthesis with database persistence.
"""

import time
from typing import Optional, Dict, Any

from src.integrations.openai_synthesis_client import OpenAISynthesisClient
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.synthesis_repository import SynthesisRepository
from src.models.conversation import ConversationStatus
from src.utils.logger import logger


class SynthesisService:
    """
    Service for meeting synthesis generation.

    Flow:
    1. Get conversation and validate transcript exists
    2. Call GPT-4 to synthesize transcript
    3. Store synthesis in database
    4. Update conversation status
    5. Return structured synthesis
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        synthesis_repo: SynthesisRepository,
        synthesis_client: Optional[OpenAISynthesisClient] = None
    ):
        """
        Initialize synthesis service.

        Args:
            conversation_repo: Repository for conversation persistence
            synthesis_repo: Repository for synthesis persistence
            synthesis_client: OpenAI synthesis client (injected)
        """
        self.conversation_repo = conversation_repo
        self.synthesis_repo = synthesis_repo
        self.synthesis_client = synthesis_client or OpenAISynthesisClient()

    def generate_synthesis(
        self,
        conversation_id: str,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate synthesis for a conversation's transcript.

        Args:
            conversation_id: ID of conversation to synthesize
            force_regenerate: If True, regenerate even if synthesis exists

        Returns:
            Dictionary containing:
                - synthesis_id: ID of created/existing synthesis
                - summary: Meeting summary
                - key_decisions: List of decisions
                - action_items: List of action items
                - open_questions: List of questions
                - key_topics: List of topics
                - llm_model: Model used
                - llm_tokens_used: Tokens consumed
                - processing_time_seconds: Time taken

        Raises:
            ValueError: If conversation not found or no transcript available
            Exception: If synthesis generation fails
        """
        logger.info(
            "synthesis_generation_started",
            conversation_id=conversation_id,
            force_regenerate=force_regenerate
        )

        # Get conversation
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            logger.error("conversation_not_found", conversation_id=conversation_id)
            raise ValueError(f"Conversation {conversation_id} not found")

        # Check if transcript exists
        if not conversation.transcript:
            logger.error(
                "no_transcript_available",
                conversation_id=conversation_id,
                status=conversation.status
            )
            raise ValueError(
                f"No transcript available for conversation {conversation_id}. "
                f"Status: {conversation.status}. Please transcribe first."
            )

        # Check if synthesis already exists
        existing_synthesis = self.synthesis_repo.get_by_conversation_id(conversation_id)
        if existing_synthesis and not force_regenerate:
            logger.info(
                "synthesis_already_exists",
                conversation_id=conversation_id,
                synthesis_id=existing_synthesis.id
            )
            return {
                "synthesis_id": existing_synthesis.id,
                "summary": existing_synthesis.summary,
                "key_decisions": existing_synthesis.key_decisions,
                "action_items": existing_synthesis.action_items,
                "open_questions": existing_synthesis.open_questions,
                "key_topics": existing_synthesis.key_topics,
                "llm_model": existing_synthesis.llm_model,
                "llm_tokens_used": existing_synthesis.llm_tokens_used,
                "processing_time_seconds": existing_synthesis.processing_time_seconds
            }

        # Update conversation status to SYNTHESIZING
        self.conversation_repo.update(
            conversation_id,
            status=ConversationStatus.SYNTHESIZING,
            synthesis_provider="openai_gpt4"
        )

        start_time = time.time()

        try:
            # Generate synthesis using GPT-4
            synthesis_result = self.synthesis_client.synthesize_transcript(
                transcript=conversation.transcript,
                conversation_title=conversation.title
            )

            # Calculate summary word count
            summary_word_count = len(synthesis_result["summary"].split())

            # Store or update synthesis in database
            if existing_synthesis:
                # Update existing synthesis
                synthesis = self.synthesis_repo.update(
                    existing_synthesis.id,
                    summary=synthesis_result["summary"],
                    summary_word_count=summary_word_count,
                    key_decisions=synthesis_result["key_decisions"],
                    action_items=synthesis_result["action_items"],
                    open_questions=synthesis_result["open_questions"],
                    key_topics=synthesis_result["key_topics"],
                    llm_model=synthesis_result["llm_model"],
                    llm_tokens_used=synthesis_result["llm_tokens_used"],
                    processing_time_seconds=synthesis_result["processing_time_seconds"]
                )
                logger.info(
                    "synthesis_regenerated",
                    conversation_id=conversation_id,
                    synthesis_id=synthesis.id
                )
            else:
                # Create new synthesis
                synthesis = self.synthesis_repo.create(
                    conversation_id=conversation_id,
                    summary=synthesis_result["summary"],
                    summary_word_count=summary_word_count,
                    key_decisions=synthesis_result["key_decisions"],
                    action_items=synthesis_result["action_items"],
                    open_questions=synthesis_result["open_questions"],
                    key_topics=synthesis_result["key_topics"],
                    llm_model=synthesis_result["llm_model"],
                    llm_tokens_used=synthesis_result["llm_tokens_used"],
                    processing_time_seconds=synthesis_result["processing_time_seconds"]
                )
                logger.info(
                    "synthesis_created",
                    conversation_id=conversation_id,
                    synthesis_id=synthesis.id
                )

            # Update conversation status to COMPLETED
            total_processing_time = int(time.time() - start_time)
            self.conversation_repo.update(
                conversation_id,
                status=ConversationStatus.COMPLETED,
                processing_time_seconds=total_processing_time
            )

            logger.info(
                "synthesis_generation_completed",
                conversation_id=conversation_id,
                synthesis_id=synthesis.id,
                total_time_seconds=total_processing_time,
                decisions_count=len(synthesis_result["key_decisions"]),
                action_items_count=len(synthesis_result["action_items"])
            )

            return {
                "synthesis_id": synthesis.id,
                "summary": synthesis_result["summary"],
                "key_decisions": synthesis_result["key_decisions"],
                "action_items": synthesis_result["action_items"],
                "open_questions": synthesis_result["open_questions"],
                "key_topics": synthesis_result["key_topics"],
                "llm_model": synthesis_result["llm_model"],
                "llm_tokens_used": synthesis_result["llm_tokens_used"],
                "processing_time_seconds": synthesis_result["processing_time_seconds"]
            }

        except Exception as e:
            # Synthesis failed - update conversation status
            processing_time = int(time.time() - start_time)
            error_message = f"Synthesis failed: {str(e)}"

            logger.error(
                "synthesis_generation_failed",
                conversation_id=conversation_id,
                error=str(e),
                processing_time_seconds=processing_time,
                exc_info=True
            )

            self.conversation_repo.update(
                conversation_id,
                status=ConversationStatus.FAILED,
                error_message=error_message,
                processing_time_seconds=processing_time
            )

            raise

    def get_synthesis(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get existing synthesis for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Synthesis dictionary if exists, None otherwise
        """
        synthesis = self.synthesis_repo.get_by_conversation_id(conversation_id)
        if not synthesis:
            return None

        return {
            "synthesis_id": synthesis.id,
            "conversation_id": synthesis.conversation_id,
            "summary": synthesis.summary,
            "summary_word_count": synthesis.summary_word_count,
            "key_decisions": synthesis.key_decisions,
            "action_items": synthesis.action_items,
            "open_questions": synthesis.open_questions,
            "key_topics": synthesis.key_topics,
            "llm_model": synthesis.llm_model,
            "llm_tokens_used": synthesis.llm_tokens_used,
            "processing_time_seconds": synthesis.processing_time_seconds,
            "created_at": synthesis.created_at.isoformat(),
            "updated_at": synthesis.updated_at.isoformat()
        }

    def estimate_cost(self, conversation_id: str) -> float:
        """
        Estimate synthesis cost for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Estimated cost in USD

        Raises:
            ValueError: If conversation not found or no transcript
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if not conversation.transcript_word_count:
            raise ValueError("No transcript available for cost estimation")

        return self.synthesis_client.estimate_cost(conversation.transcript_word_count)

    def health_check(self) -> bool:
        """
        Check health of synthesis service.

        Returns:
            True if service is healthy, False otherwise
        """
        return self.synthesis_client.health_check()
