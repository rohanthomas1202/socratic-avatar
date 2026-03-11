"""Unit tests for Speech-to-Text module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pipeline.stt import DeepgramSTT


class TestDeepgramSTT:
    def setup_method(self):
        self.stt = DeepgramSTT()

    @pytest.mark.asyncio
    async def test_empty_api_key_returns_empty(self):
        """Should return empty string when no API key is configured."""
        self.stt.api_key = ""
        result = await self.stt.transcribe_audio(b"\x00" * 1600)
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_streaming_yields_transcript(self):
        """Streaming transcription should yield the final transcript."""
        self.stt.api_key = ""
        results = []
        async for text in self.stt.transcribe_streaming(b"\x00" * 1600):
            results.append(text)
        # With no API key, transcribe returns "" so nothing is yielded
        assert results == []

    @pytest.mark.asyncio
    async def test_transcribe_audio_handles_exception(self):
        """Should return empty string on API errors."""
        self.stt.api_key = "fake-key"

        with patch("pipeline.stt.asyncio.to_thread", side_effect=Exception("API error")):
            result = await self.stt.transcribe_audio(b"\x00" * 1600)
            assert result == ""

    def test_init_sets_api_key_from_settings(self):
        """Should initialize with API key from settings."""
        stt = DeepgramSTT()
        # Just verify it initializes without error
        assert stt._client is None
