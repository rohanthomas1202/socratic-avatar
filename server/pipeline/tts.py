"""Text-to-Speech using ElevenLabs v2 streaming API.

Converts text sentences to PCM16 audio chunks via ElevenLabs'
streaming WebSocket interface for low-latency speech synthesis.
"""

import asyncio
import logging
import re
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

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Strip markdown formatting so TTS reads naturally."""
        # Remove bold/italic markers: **text** → text, *text* → text, __text__ → text
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
        # Remove markdown headers: ### Header → Header
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove inline code backticks: `code` → code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove markdown links: [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove bullet markers: - item or * item → item
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        # Remove numbered list markers: 1. item → item
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        # Collapse multiple spaces/newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

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

        text = self._clean_for_speech(text)
        if not text:
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

        text = self._clean_for_speech(text)
        if not text:
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
