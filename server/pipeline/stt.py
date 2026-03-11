"""Speech-to-Text using AssemblyAI.

Converts audio bytes to text transcripts. Supports both batch
transcription and real-time streaming for live captions.
"""

import asyncio
import io
import logging
import wave
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)


class AssemblyAISTT:
    """AssemblyAI speech-to-text client."""

    def __init__(self):
        self.api_key = settings.assemblyai_api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            import assemblyai as aai
            aai.settings.api_key = self.api_key
            self._client = aai.Transcriber()
        return self._client

    def _pcm16_to_wav(self, audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
        """Wrap raw PCM16 bytes in a WAV container for the API."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
        return buf.getvalue()

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe a complete audio buffer to text.

        Args:
            audio_bytes: Raw PCM16 audio (16kHz, mono).

        Returns:
            Transcribed text string.
        """
        if not self.api_key:
            logger.warning("No AssemblyAI API key set, returning empty transcript")
            return ""

        try:
            import assemblyai as aai

            wav_bytes = self._pcm16_to_wav(audio_bytes)
            config = aai.TranscriptionConfig(
                language_code="en",
                punctuate=True,
                format_text=True,
            )

            transcriber = self._get_client()
            transcript = await asyncio.to_thread(
                lambda: transcriber.transcribe(wav_bytes, config=config)
            )

            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"AssemblyAI error: {transcript.error}")
                return ""

            text = transcript.text or ""
            logger.info(f"STT transcript: {text}")
            return text

        except Exception as e:
            logger.error(f"AssemblyAI STT error: {e}")
            return ""

    async def transcribe_streaming(self, audio_bytes: bytes) -> AsyncGenerator[str, None]:
        """Stream transcription results.

        Currently wraps batch transcription. Real-time streaming
        can be added using AssemblyAI's real-time WebSocket API.

        Args:
            audio_bytes: Raw PCM16 audio (16kHz, mono).

        Yields:
            Transcript strings.
        """
        transcript = await self.transcribe_audio(audio_bytes)
        if transcript:
            yield transcript
