"""Fast LLM client using Groq (Llama-3.3-70B).

Used for quick responses like acknowledgments and short follow-up questions.
Optimized for low TTFT (~80ms) at the cost of slightly lower quality
compared to GPT-4o-mini.
"""

import logging
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are a Socratic tutor. Your role is to help students discover answers through guided questioning.

Rules:
- NEVER give direct answers
- Always respond with a guiding question
- Build on what the student just said
- Keep responses concise (1-3 sentences)
- If the student is wrong, ask a question that reveals the error
- If the student is right, ask them to explain WHY
- Use age-appropriate language (middle school level)"""


class GroqLLM:
    """Groq Llama-3.3-70B streaming LLM client."""

    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.system_prompt = system_prompt
        self._client = None

    def _get_client(self):
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Generate a complete response (non-streaming).

        Args:
            user_message: The student's transcribed speech.
            conversation_history: Prior messages for context.

        Returns:
            Complete LLM response text.
        """
        if not self.api_key:
            logger.warning("No Groq API key set, returning placeholder")
            return "That's an interesting thought. Can you tell me more about why you think that?"

        import asyncio
        messages = self._build_messages(user_message, conversation_history)

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=256,
                )
            )
            text = response.choices[0].message.content
            logger.info(f"LLM response: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"Groq LLM error: {e}")
            return "That's interesting. Can you tell me more?"

    async def generate_stream(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response tokens.

        Args:
            user_message: The student's transcribed speech.
            conversation_history: Prior messages for context.

        Yields:
            Token strings as they're generated.
        """
        if not self.api_key:
            logger.warning("No Groq API key set, yielding placeholder")
            yield "That's an interesting thought. Can you tell me more about why you think that?"
            return

        import asyncio
        messages = self._build_messages(user_message, conversation_history)

        try:
            client = self._get_client()
            stream = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=256,
                    stream=True,
                )
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"Groq LLM streaming error: {e}")
            yield "That's interesting. Can you tell me more?"

    def _build_messages(
        self,
        user_message: str,
        conversation_history: list[dict] | None,
    ) -> list[dict]:
        """Build the messages array for the API call."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        return messages
