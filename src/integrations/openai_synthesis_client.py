"""
OpenAI GPT-4 client for meeting synthesis.
Extracts structured insights from transcripts: summary, decisions, action items, questions.
"""

import time
import json
from typing import Optional, Dict, Any
from openai import OpenAI, OpenAIError

from src.config import settings
from src.utils.logger import logger


class OpenAISynthesisClient:
    """
    Client for GPT-4 meeting synthesis.
    Transforms raw transcripts into actionable insights.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI synthesis client.

        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        """
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.openai_model_synthesis
        self.extraction_model = settings.openai_model_extraction

    def synthesize_transcript(
        self,
        transcript: str,
        conversation_title: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Synthesize meeting transcript into structured insights.

        Args:
            transcript: Meeting transcript text
            conversation_title: Optional meeting title for context
            max_retries: Maximum retry attempts on failure

        Returns:
            Dictionary containing:
                - summary: 3-sentence meeting summary
                - key_decisions: List of decisions made
                - action_items: List of action items with owners
                - open_questions: List of unanswered questions
                - key_topics: List of main topics discussed
                - llm_model: Model used for synthesis
                - llm_tokens_used: Total tokens consumed
                - processing_time_seconds: Time taken

        Raises:
            OpenAIError: If synthesis fails after all retries
            ValueError: If transcript is empty or too short
        """
        # Validate input
        if not transcript or len(transcript.strip()) < 50:
            raise ValueError("Transcript too short for synthesis (minimum 50 characters)")

        word_count = len(transcript.split())
        logger.info(
            "synthesis_started",
            model=self.model,
            word_count=word_count,
            conversation_title=conversation_title
        )

        start_time = time.time()
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Create synthesis prompt
                system_prompt = self._build_system_prompt()
                user_prompt = self._build_user_prompt(transcript, conversation_title)

                # Call GPT-4
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # Low temperature for consistent extraction
                    max_tokens=2000,  # Enough for comprehensive synthesis
                    response_format={"type": "json_object"}  # Force JSON response
                )

                # Parse response
                content = response.choices[0].message.content
                synthesis_data = json.loads(content)

                # Track metrics
                processing_time = time.time() - start_time
                tokens_used = response.usage.total_tokens

                result = {
                    "summary": synthesis_data.get("summary", ""),
                    "key_decisions": synthesis_data.get("key_decisions", []),
                    "action_items": synthesis_data.get("action_items", []),
                    "open_questions": synthesis_data.get("open_questions", []),
                    "key_topics": synthesis_data.get("key_topics", []),
                    "llm_model": self.model,
                    "llm_tokens_used": tokens_used,
                    "processing_time_seconds": processing_time
                }

                logger.info(
                    "synthesis_completed",
                    model=self.model,
                    tokens_used=tokens_used,
                    processing_time_seconds=processing_time,
                    decisions_count=len(result["key_decisions"]),
                    action_items_count=len(result["action_items"]),
                    questions_count=len(result["open_questions"])
                )

                return result

            except OpenAIError as e:
                last_error = e
                logger.warning(
                    "synthesis_retry",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e)
                )

                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(
                        "synthesis_retry_wait",
                        wait_seconds=wait_time,
                        next_attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                else:
                    # All retries exhausted
                    logger.error(
                        "synthesis_failed",
                        attempts=max_retries,
                        error=str(e),
                        exc_info=True
                    )
                    raise

            except json.JSONDecodeError as e:
                last_error = e
                logger.error(
                    "synthesis_json_parse_error",
                    attempt=attempt,
                    error=str(e),
                    response_content=content if 'content' in locals() else None
                )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise OpenAIError(f"Failed to parse synthesis response as JSON: {str(e)}")

        # Should never reach here, but for type safety
        raise last_error or OpenAIError("Synthesis failed")

    def _build_system_prompt(self) -> str:
        """
        Build system prompt for synthesis.

        Returns:
            System prompt string
        """
        return """You are an expert meeting analyst. Your task is to analyze meeting transcripts and extract structured insights.

Extract the following information from the meeting transcript:

1. **Summary**: Write a concise 3-sentence summary capturing the meeting's purpose, main discussions, and outcomes.

2. **Key Decisions**: List all decisions that were explicitly made during the meeting. Each decision should be a clear, actionable statement.

3. **Action Items**: List all tasks or actions that were assigned. For each action item, include:
   - task: What needs to be done
   - owner: Who is responsible (if mentioned)
   - due_date: When it's due (if mentioned)

4. **Open Questions**: List any questions raised that were NOT answered during the meeting.

5. **Key Topics**: List 3-5 main topics or themes discussed in the meeting.

Return your response as valid JSON with this structure:
{
  "summary": "string",
  "key_decisions": ["string", ...],
  "action_items": [
    {"task": "string", "owner": "string", "due_date": "string"},
    ...
  ],
  "open_questions": ["string", ...],
  "key_topics": ["string", ...]
}

Guidelines:
- Be precise and factual - only include what was actually discussed
- If a category has no items, return an empty array
- For action items without owner/due_date, use "Not specified"
- Keep each item concise but complete
- Focus on substance, not small talk or off-topic conversations"""

    def _build_user_prompt(
        self,
        transcript: str,
        conversation_title: Optional[str] = None
    ) -> str:
        """
        Build user prompt with transcript.

        Args:
            transcript: Meeting transcript
            conversation_title: Optional meeting title

        Returns:
            User prompt string
        """
        title_context = f"\nMeeting Title: {conversation_title}\n" if conversation_title else ""

        return f"""{title_context}
Please analyze the following meeting transcript and extract structured insights:

---TRANSCRIPT START---
{transcript}
---TRANSCRIPT END---

Provide your analysis as JSON following the specified structure."""

    def estimate_cost(
        self,
        transcript_word_count: int,
        model: Optional[str] = None
    ) -> float:
        """
        Estimate synthesis cost based on transcript length.

        GPT-4 Turbo pricing (2026):
        - Input: $0.01 per 1K tokens
        - Output: $0.03 per 1K tokens

        Rough estimate: 1 word ≈ 1.3 tokens

        Args:
            transcript_word_count: Number of words in transcript
            model: Model to estimate for (defaults to synthesis model)

        Returns:
            Estimated cost in USD
        """
        model = model or self.model

        # Estimate tokens
        input_tokens = transcript_word_count * 1.3  # Transcript + prompt
        output_tokens = 500  # Typical synthesis output

        # Pricing for GPT-4 Turbo
        if "gpt-4" in model:
            input_cost_per_1k = 0.01
            output_cost_per_1k = 0.03
        else:
            # GPT-3.5 fallback
            input_cost_per_1k = 0.0005
            output_cost_per_1k = 0.0015

        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k

        return input_cost + output_cost

    def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Simple completion to verify API access
            self.client.chat.completions.create(
                model=self.extraction_model,  # Use cheaper model for health check
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            logger.info("openai_synthesis_health_check_passed")
            return True
        except Exception as e:
            logger.error("openai_synthesis_health_check_failed", error=str(e))
            return False
