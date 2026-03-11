"""Text-to-Speech using ElevenLabs v2 streaming API.

Converts text sentences to PCM16 audio chunks via ElevenLabs'
streaming WebSocket interface for low-latency speech synthesis.
"""

import asyncio
import logging
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    """ElevenLabs v2 streaming text-to-speech client."""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.tts_voice_id
        self.model_id = settings.tts_model_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from elevenlabs import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio bytes (non-streaming).

        Args:
            text: Text to convert to speech.

        Returns:
            Audio bytes (MP3 format from ElevenLabs, or empty on error).
        """
        if not self.api_key:
            logger.warning("No ElevenLabs API key set, returning empty audio")
            return b""

        try:
            client = self._get_client()
            audio_iter = await asyncio.to_thread(
                lambda: client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text,
                    model_id=self.model_id,
                    output_format="pcm_16000",
                )
            )
            # Collect all audio chunks
            audio_chunks = []
            for chunk in audio_iter:
                audio_chunks.append(chunk)
            audio = b"".join(audio_chunks)
            logger.info(f"TTS synthesized {len(audio)} PCM16 bytes for: {text[:50]}...")
            return audio

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return b""

    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks as they're synthesized.

        Args:
            text: Text to convert to speech.

        Yields:
            Audio bytes chunks as they become available.
        """
        if not self.api_key:
            logger.warning("No ElevenLabs API key set, yielding empty")
            return

        try:
            client = self._get_client()
            audio_iter = await asyncio.to_thread(
                lambda: client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text,
                    model_id=self.model_id,
                    output_format="pcm_16000",
                )
            )

            for chunk in audio_iter:
                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"ElevenLabs TTS streaming error: {e}")
