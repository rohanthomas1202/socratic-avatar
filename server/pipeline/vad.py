"""Voice Activity Detection using Silero VAD.

Detects speech start/end in audio buffers to determine when the user
has finished speaking and the pipeline should process their utterance.
"""

import numpy as np


class VoiceActivityDetector:
    """Silero VAD wrapper for detecting speech boundaries in audio streams."""

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_silence_ms: int = 300,
        min_speech_ms: int = 250,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_silence_samples = int(min_silence_ms * sample_rate / 1000)
        self.min_speech_samples = int(min_speech_ms * sample_rate / 1000)

        self._model = None
        self._is_speaking = False
        self._silence_counter = 0
        self._speech_counter = 0
        self._audio_buffer: list[bytes] = []

    def _load_model(self):
        """Lazy-load Silero VAD model."""
        if self._model is not None:
            return
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            self._model = model
            self._get_speech_timestamps = utils[0]
        except ImportError:
            # Fallback: energy-based VAD when torch is not available
            self._model = "energy_fallback"

    def _energy_vad(self, audio_chunk: np.ndarray) -> float:
        """Simple energy-based VAD fallback when Silero is unavailable."""
        if len(audio_chunk) == 0:
            return 0.0
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        # Normalize to 0-1 range (assuming int16 input)
        return min(rms / 3000.0, 1.0)

    def _get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """Get speech probability for an audio chunk."""
        self._load_model()

        if self._model == "energy_fallback":
            return self._energy_vad(audio_chunk)

        import torch
        audio_tensor = torch.from_numpy(audio_chunk.astype(np.float32) / 32768.0)
        if len(audio_tensor.shape) == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        prob = self._model(audio_tensor, self.sample_rate).item()
        return prob

    def process_chunk(self, audio_bytes: bytes) -> dict:
        """Process an audio chunk and return VAD state.

        Args:
            audio_bytes: Raw PCM16 audio bytes (16kHz, mono).

        Returns:
            dict with keys:
                - is_speech: bool, whether current chunk contains speech
                - speech_ended: bool, whether speech just ended (trigger pipeline)
                - speech_started: bool, whether speech just started
        """
        audio_chunk = np.frombuffer(audio_bytes, dtype=np.int16)
        probability = self._get_speech_probability(audio_chunk)
        is_speech = bool(probability >= self.threshold)

        result = {
            "is_speech": is_speech,
            "speech_ended": False,
            "speech_started": False,
            "probability": probability,
        }

        if is_speech:
            self._speech_counter += len(audio_chunk)
            self._silence_counter = 0
            self._audio_buffer.append(audio_bytes)

            if not self._is_speaking and self._speech_counter >= self.min_speech_samples:
                self._is_speaking = True
                result["speech_started"] = True
        else:
            self._silence_counter += len(audio_chunk)
            self._speech_counter = 0

            if self._is_speaking and self._silence_counter >= self.min_silence_samples:
                self._is_speaking = False
                result["speech_ended"] = True

        return result

    def get_buffered_audio(self) -> bytes:
        """Get all buffered audio since speech started and clear buffer."""
        audio = b"".join(self._audio_buffer)
        self._audio_buffer.clear()
        return audio

    def reset(self):
        """Reset VAD state for a new turn."""
        self._is_speaking = False
        self._silence_counter = 0
        self._speech_counter = 0
        self._audio_buffer.clear()
        if self._model is not None and self._model != "energy_fallback":
            self._model.reset_states()
