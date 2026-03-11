"""Unit tests for Voice Activity Detection."""

import numpy as np
import pytest
from pipeline.vad import VoiceActivityDetector


class TestVoiceActivityDetector:
    def setup_method(self):
        self.vad = VoiceActivityDetector(
            sample_rate=16000,
            threshold=0.5,
            min_silence_ms=300,
            min_speech_ms=250,
        )

    def _make_silence(self, duration_ms: int = 100) -> bytes:
        """Generate silent audio bytes."""
        num_samples = int(16000 * duration_ms / 1000)
        # Low amplitude noise (not perfectly silent, more realistic)
        audio = np.random.randint(-50, 50, num_samples, dtype=np.int16)
        return audio.tobytes()

    def _make_speech(self, duration_ms: int = 100, amplitude: int = 8000) -> bytes:
        """Generate speech-like audio bytes (high energy sine wave)."""
        num_samples = int(16000 * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, num_samples)
        # 300Hz sine wave at specified amplitude
        audio = (amplitude * np.sin(2 * np.pi * 300 * t)).astype(np.int16)
        return audio.tobytes()

    def test_init_defaults(self):
        vad = VoiceActivityDetector()
        assert vad.sample_rate == 16000
        assert vad.threshold == 0.5
        assert not vad._is_speaking

    def test_silence_returns_no_speech(self):
        """Silence should not trigger speech detection."""
        result = self.vad.process_chunk(self._make_silence(100))
        assert result["is_speech"] is False
        assert result["speech_started"] is False
        assert result["speech_ended"] is False

    def test_speech_detection_with_energy_fallback(self):
        """High-energy audio should be detected as speech by energy VAD."""
        # Force energy fallback
        self.vad._model = "energy_fallback"

        result = self.vad.process_chunk(self._make_speech(300, amplitude=10000))
        assert result["is_speech"] is True
        assert result["probability"] > 0.5

    def test_silence_detection_with_energy_fallback(self):
        """Low-energy audio should not be detected as speech."""
        self.vad._model = "energy_fallback"

        result = self.vad.process_chunk(self._make_silence(100))
        assert result["is_speech"] is False
        assert result["probability"] < 0.5

    def test_speech_start_requires_min_duration(self):
        """Speech start should only trigger after min_speech_ms of speech."""
        self.vad._model = "energy_fallback"

        # Short burst — not enough for speech_started
        result = self.vad.process_chunk(self._make_speech(100, amplitude=10000))
        assert result["speech_started"] is False

        # Longer speech — should trigger speech_started
        result = self.vad.process_chunk(self._make_speech(200, amplitude=10000))
        assert result["speech_started"] is True

    def test_speech_end_after_silence(self):
        """Speech end should trigger after min_silence_ms of silence."""
        self.vad._model = "energy_fallback"

        # Start speaking
        self.vad.process_chunk(self._make_speech(300, amplitude=10000))

        # Short silence — not enough to end
        result = self.vad.process_chunk(self._make_silence(100))
        assert result["speech_ended"] is False

        # More silence — should trigger speech_ended
        result = self.vad.process_chunk(self._make_silence(250))
        assert result["speech_ended"] is True

    def test_get_buffered_audio(self):
        """Buffered audio should accumulate during speech and clear on get."""
        self.vad._model = "energy_fallback"

        speech_chunk = self._make_speech(300, amplitude=10000)
        self.vad.process_chunk(speech_chunk)

        buffered = self.vad.get_buffered_audio()
        assert len(buffered) > 0

        # Buffer should be empty after get
        assert len(self.vad.get_buffered_audio()) == 0

    def test_reset_clears_state(self):
        """Reset should clear all internal state."""
        self.vad._model = "energy_fallback"

        self.vad.process_chunk(self._make_speech(300, amplitude=10000))
        assert self.vad._is_speaking is True

        self.vad.reset()
        assert self.vad._is_speaking is False
        assert len(self.vad._audio_buffer) == 0
        assert self.vad._silence_counter == 0
        assert self.vad._speech_counter == 0

    def test_energy_vad_empty_chunk(self):
        """Energy VAD should handle empty audio gracefully."""
        result = self.vad._energy_vad(np.array([], dtype=np.int16))
        assert result == 0.0

    def test_probability_in_result(self):
        """Result should include speech probability."""
        self.vad._model = "energy_fallback"
        result = self.vad.process_chunk(self._make_speech(100, amplitude=5000))
        assert "probability" in result
        assert 0.0 <= result["probability"] <= 1.0
