"""Integration tests for LLM streaming.

These tests require valid API keys in .env.
Skip if no API keys are configured.
"""

import pytest
from config import settings
from pipeline.llm_fast import GroqLLM
from pipeline.llm_quality import ClaudeLLM

requires_groq = pytest.mark.skipif(
    not settings.groq_api_key,
    reason="GROQ_API_KEY not set"
)

requires_anthropic = pytest.mark.skipif(
    not settings.anthropic_api_key,
    reason="ANTHROPIC_API_KEY not set"
)


@requires_groq
class TestGroqStreaming:
    def setup_method(self):
        self.llm = GroqLLM()

    @pytest.mark.asyncio
    async def test_generate_returns_text(self):
        """Groq should return a non-empty response."""
        result = await self.llm.generate("What is 2 + 2?")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_stream_yields_tokens(self):
        """Groq streaming should yield at least one token."""
        tokens = []
        async for token in self.llm.generate_stream("What is 2 + 2?"):
            tokens.append(token)
        assert len(tokens) > 0
        assert len("".join(tokens)) > 0


@requires_anthropic
class TestClaudeStreaming:
    def setup_method(self):
        self.llm = ClaudeLLM(system_prompt="You are a helpful tutor.")

    @pytest.mark.asyncio
    async def test_generate_returns_text(self):
        """Claude should return a non-empty response."""
        result = await self.llm.generate("What is 2 + 2?")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_stream_yields_tokens(self):
        """Claude streaming should yield at least one token."""
        tokens = []
        async for token in self.llm.generate_stream("What is 2 + 2?"):
            tokens.append(token)
        assert len(tokens) > 0
