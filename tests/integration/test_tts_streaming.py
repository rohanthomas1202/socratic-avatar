"""Integration tests for TTS streaming.

These tests require a valid ELEVENLABS_API_KEY in .env.
Skip if no API key is configured.
"""

import pytest
from config import settings
from pipeline.tts import ElevenLabsTTS

requires_elevenlabs = pytest.mark.skipif(
    not settings.elevenlabs_api_key,
    reason="ELEVENLABS_API_KEY not set"
)


@requires_elevenlabs
class TestTTSStreaming:
    def setup_method(self):
        self.tts = ElevenLabsTTS()

    @pytest.mark.asyncio
    async def test_synthesize_returns_audio(self):
        """TTS should return non-empty audio bytes."""
        audio = await self.tts.synthesize("Hello, this is a test.")
        assert isinstance(audio, bytes)
        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_streaming_yields_chunks(self):
        """TTS streaming should yield at least one audio chunk."""
        chunks = []
        async for chunk in self.tts.synthesize_streaming("Hello, this is a test."):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert all(isinstance(c, bytes) for c in chunks)
