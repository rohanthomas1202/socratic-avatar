"""Dual-model LLM router.

Routes requests to the appropriate LLM based on the Socratic state:
- Groq (fast): OPENING, CONFIRM, CLOSE, and ACK responses — speed matters
- Claude (quality): SCAFFOLD, REDIRECT, DEEPEN, PROBE — pedagogical reasoning matters
"""

import logging
from typing import AsyncGenerator

from pipeline.llm_fast import GroqLLM
from pipeline.llm_quality import ClaudeLLM
from socratic.state_machine import SocraticState

logger = logging.getLogger(__name__)

# States that require high-quality pedagogical reasoning
QUALITY_STATES = {
    SocraticState.SCAFFOLD,
    SocraticState.REDIRECT,
    SocraticState.DEEPEN,
    SocraticState.PROBE,
}

# States where speed matters more than depth
FAST_STATES = {
    SocraticState.OPENING,
    SocraticState.CONFIRM,
    SocraticState.CLOSE,
}


class LLMRouter:
    """Routes LLM requests to Groq (fast) or Claude (quality) based on state."""

    def __init__(self):
        self._groq: GroqLLM | None = None
        self._claude: ClaudeLLM | None = None

    def _get_groq(self, system_prompt: str) -> GroqLLM:
        if self._groq is None or self._groq.system_prompt != system_prompt:
            self._groq = GroqLLM(system_prompt=system_prompt)
        return self._groq

    def _get_claude(self, system_prompt: str) -> ClaudeLLM:
        if self._claude is None or self._claude.system_prompt != system_prompt:
            self._claude = ClaudeLLM(system_prompt=system_prompt)
        return self._claude

    def select_model(self, state: SocraticState) -> str:
        """Return which model will be used for this state."""
        if state in QUALITY_STATES:
            return "claude"
        return "groq"

    async def generate_stream(
        self,
        user_message: str,
        conversation_history: list[dict] | None,
        system_prompt: str,
        state: SocraticState,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from the appropriate LLM.

        Args:
            user_message: Student's transcribed text.
            conversation_history: Prior conversation messages.
            system_prompt: State-specific system prompt.
            state: Current Socratic state (determines routing).

        Yields:
            Token strings as they're generated.
        """
        model_name = self.select_model(state)
        logger.info(f"Routing to {model_name} for state={state.value}")

        if model_name == "claude":
            llm = self._get_claude(system_prompt)
        else:
            llm = self._get_groq(system_prompt)

        async for token in llm.generate_stream(
            user_message=user_message,
            conversation_history=conversation_history,
        ):
            yield token

    async def generate(
        self,
        user_message: str,
        conversation_history: list[dict] | None,
        system_prompt: str,
        state: SocraticState,
    ) -> str:
        """Generate a complete response from the appropriate LLM."""
        model_name = self.select_model(state)
        logger.info(f"Routing to {model_name} for state={state.value}")

        if model_name == "claude":
            llm = self._get_claude(system_prompt)
        else:
            llm = self._get_groq(system_prompt)

        return await llm.generate(
            user_message=user_message,
            conversation_history=conversation_history,
        )
