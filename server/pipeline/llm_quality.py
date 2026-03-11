"""Quality LLM client using Anthropic Claude.

Used for complex scaffolding and redirecting responses where
pedagogical reasoning quality matters more than raw speed.
Claude excels at Socratic questioning and educational dialogue.
"""

import asyncio
import logging
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)


class ClaudeLLM:
    """Anthropic Claude streaming LLM client."""

    def __init__(self, system_prompt: str = ""):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.system_prompt = system_prompt
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Generate a complete response (non-streaming)."""
        if not self.api_key:
            logger.warning("No Anthropic API key set, returning placeholder")
            return "That's a really interesting thought. What makes you think that?"

        messages = self._build_messages(user_message, conversation_history)

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                lambda: client.messages.create(
                    model=self.model,
                    max_tokens=256,
                    system=self.system_prompt if self.system_prompt else "",
                    messages=messages,
                )
            )
            text = response.content[0].text
            logger.info(f"Claude response: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"Claude LLM error: {e}")
            return "That's interesting. Can you explain your thinking?"

    async def generate_stream(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response tokens."""
        if not self.api_key:
            logger.warning("No Anthropic API key set, yielding placeholder")
            yield "That's a really interesting thought. What makes you think that?"
            return

        messages = self._build_messages(user_message, conversation_history)

        try:
            client = self._get_client()
            with client.messages.stream(
                model=self.model,
                max_tokens=256,
                system=self.system_prompt if self.system_prompt else "",
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude LLM streaming error: {e}")
            yield "That's interesting. Can you explain your thinking?"

    def _build_messages(
        self,
        user_message: str,
        conversation_history: list[dict] | None,
    ) -> list[dict]:
        """Build messages array for Claude API (no system role in messages)."""
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        return messages
