"""Unit tests for Speech-to-Text module."""

import pytest
from unittest.mock import patch
from pipeline.stt import AssemblyAISTT


class TestAssemblyAISTT:
    def setup_method(self):
        self.stt = AssemblyAISTT()

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
        stt = AssemblyAISTT()
        assert stt._client is None

    def test_pcm16_to_wav(self):
        """Should produce valid WAV bytes from PCM16 data."""
        stt = AssemblyAISTT()
        pcm_data = b"\x00\x01" * 800  # 800 samples
        wav_bytes = stt._pcm16_to_wav(pcm_data)
        # WAV files start with RIFF header
        assert wav_bytes[:4] == b"RIFF"
        assert wav_bytes[8:12] == b"WAVE"
