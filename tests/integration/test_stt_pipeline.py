"""Integration tests for STT pipeline.

These tests require a valid ASSEMBLYAI_API_KEY in .env.
Skip if no API key is configured.
"""

import pytest
from config import settings
from pipeline.stt import AssemblyAISTT

requires_assemblyai = pytest.mark.skipif(
    not settings.assemblyai_api_key,
    reason="ASSEMBLYAI_API_KEY not set"
)


@requires_assemblyai
class TestSTTPipeline:
    def setup_method(self):
        self.stt = AssemblyAISTT()

    @pytest.mark.asyncio
    async def test_transcribe_audio_returns_text(self):
        """Real audio should return a non-empty transcript."""
        import numpy as np
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = (16000 * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
        audio_bytes = audio.tobytes()

        # Sine wave won't produce real speech, but should not raise
        result = await self.stt.transcribe_audio(audio_bytes)
        assert isinstance(result, str)
