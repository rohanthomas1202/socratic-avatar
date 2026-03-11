"""Speech-to-Text using Deepgram Nova-2 streaming API.

Converts audio bytes to text transcripts via Deepgram's WebSocket
streaming interface for low-latency transcription.
"""

import asyncio
import logging
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)


class DeepgramSTT:
    """Deepgram Nova-2 streaming speech-to-text client."""

    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self._client = None

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe a complete audio buffer to text.

        Args:
            audio_bytes: Raw PCM16 audio (16kHz, mono).

        Returns:
            Transcribed text string.
        """
        if not self.api_key:
            logger.warning("No Deepgram API key set, returning empty transcript")
            return ""

        try:
            from deepgram import DeepgramClient, PrerecordedOptions

            client = DeepgramClient(self.api_key)
            options = PrerecordedOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
            )

            source = {"buffer": audio_bytes, "mimetype": "audio/raw;encoding=linear16;sample-rate=16000"}
            response = await asyncio.to_thread(
                lambda: client.listen.rest.v("1").transcribe_url(source, options)
            )

            transcript = (
                response.results.channels[0].alternatives[0].transcript
                if response.results.channels
                else ""
            )
            logger.info(f"STT transcript: {transcript}")
            return transcript

        except Exception as e:
            logger.error(f"Deepgram STT error: {e}")
            return ""

    async def transcribe_streaming(self, audio_bytes: bytes) -> AsyncGenerator[str, None]:
        """Stream transcription results as they become available.

        For Phase 2, this wraps the batch transcribe method.
        True streaming will be wired in Phase 3.

        Args:
            audio_bytes: Raw PCM16 audio (16kHz, mono).

        Yields:
            Partial and final transcript strings.
        """
        transcript = await self.transcribe_audio(audio_bytes)
        if transcript:
            yield transcript
