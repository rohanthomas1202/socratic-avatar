"""Pipeline orchestrator — manages the turn lifecycle.

Coordinates all pipeline stages for a single conversational turn:
1. Receive audio chunks from client
2. Feed to VAD → detect speech end
3. Transcribe with STT
4. Generate LLM response
5. (Phase 3: Stream to TTS → avatar)
6. Emit per-stage metrics
"""

import logging
import time
from dataclasses import dataclass, field

from pipeline.vad import VoiceActivityDetector
from pipeline.stt import DeepgramSTT
from pipeline.llm_fast import GroqLLM

logger = logging.getLogger(__name__)


@dataclass
class TurnMetrics:
    """Latency metrics for a single conversational turn."""
    turn_id: int = 0
    vad_end_ms: float = 0.0
    stt_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_total_ms: float = 0.0
    e2e_ms: float = 0.0


@dataclass
class SessionState:
    """State for an active tutoring session."""
    turn_count: int = 0
    conversation_history: list[dict] = field(default_factory=list)
    is_active: bool = True


class PipelineOrchestrator:
    """Coordinates the streaming pipeline for a tutoring session."""

    def __init__(self):
        self.vad = VoiceActivityDetector()
        self.stt = DeepgramSTT()
        self.llm = GroqLLM()
        self.session = SessionState()

    def process_audio_chunk(self, audio_bytes: bytes) -> dict:
        """Process an incoming audio chunk through VAD.

        Returns VAD state indicating whether to trigger the pipeline.
        """
        return self.vad.process_chunk(audio_bytes)

    async def process_turn(self, audio_bytes: bytes) -> dict:
        """Process a complete turn: audio → STT → LLM → response text.

        This is the Phase 2 sequential pipeline. Streaming is added in Phase 3.

        Args:
            audio_bytes: Complete audio for this turn (PCM16, 16kHz, mono).

        Returns:
            dict with transcript, response, and metrics.
        """
        self.session.turn_count += 1
        turn_id = self.session.turn_count
        t_start = time.perf_counter()

        # STT
        t_stt_start = time.perf_counter()
        transcript = await self.stt.transcribe_audio(audio_bytes)
        t_stt_end = time.perf_counter()

        if not transcript.strip():
            return {
                "turn_id": turn_id,
                "transcript": "",
                "response": "",
                "metrics": None,
            }

        # LLM
        t_llm_start = time.perf_counter()
        response = await self.llm.generate(
            user_message=transcript,
            conversation_history=self.session.conversation_history,
        )
        t_llm_end = time.perf_counter()

        # Update conversation history
        self.session.conversation_history.append({"role": "user", "content": transcript})
        self.session.conversation_history.append({"role": "assistant", "content": response})

        # Keep history manageable (last 20 messages)
        if len(self.session.conversation_history) > 20:
            self.session.conversation_history = self.session.conversation_history[-20:]

        t_end = time.perf_counter()

        metrics = TurnMetrics(
            turn_id=turn_id,
            stt_ms=(t_stt_end - t_stt_start) * 1000,
            llm_ttft_ms=(t_llm_end - t_llm_start) * 1000,
            llm_total_ms=(t_llm_end - t_llm_start) * 1000,
            e2e_ms=(t_end - t_start) * 1000,
        )

        logger.info(
            f"Turn {turn_id}: STT={metrics.stt_ms:.0f}ms, "
            f"LLM={metrics.llm_total_ms:.0f}ms, "
            f"E2E={metrics.e2e_ms:.0f}ms"
        )

        return {
            "turn_id": turn_id,
            "transcript": transcript,
            "response": response,
            "metrics": {
                "turn_id": metrics.turn_id,
                "stt_ms": round(metrics.stt_ms, 1),
                "llm_ttft_ms": round(metrics.llm_ttft_ms, 1),
                "e2e_ms": round(metrics.e2e_ms, 1),
            },
        }

    async def process_turn_streaming(self, audio_bytes: bytes):
        """Process a turn with streaming LLM output.

        Yields partial results as they become available.
        Full streaming pipeline (→ TTS → avatar) is wired in Phase 3.
        """
        self.session.turn_count += 1
        turn_id = self.session.turn_count
        t_start = time.perf_counter()

        # STT
        t_stt_start = time.perf_counter()
        transcript = await self.stt.transcribe_audio(audio_bytes)
        t_stt_end = time.perf_counter()

        if not transcript.strip():
            yield {"type": "turn_empty", "turn_id": turn_id}
            return

        yield {
            "type": "transcript",
            "turn_id": turn_id,
            "text": transcript,
            "stt_ms": round((t_stt_end - t_stt_start) * 1000, 1),
        }

        # Stream LLM tokens
        t_llm_start = time.perf_counter()
        first_token = True
        full_response = []

        async for token in self.llm.generate_stream(
            user_message=transcript,
            conversation_history=self.session.conversation_history,
        ):
            if first_token:
                ttft = (time.perf_counter() - t_llm_start) * 1000
                yield {"type": "llm_ttft", "turn_id": turn_id, "ttft_ms": round(ttft, 1)}
                first_token = False

            full_response.append(token)
            yield {"type": "token", "turn_id": turn_id, "text": token}

        t_llm_end = time.perf_counter()
        response_text = "".join(full_response)

        # Update conversation history
        self.session.conversation_history.append({"role": "user", "content": transcript})
        self.session.conversation_history.append({"role": "assistant", "content": response_text})
        if len(self.session.conversation_history) > 20:
            self.session.conversation_history = self.session.conversation_history[-20:]

        t_end = time.perf_counter()

        yield {
            "type": "turn_complete",
            "turn_id": turn_id,
            "metrics": {
                "stt_ms": round((t_stt_end - t_stt_start) * 1000, 1),
                "llm_ttft_ms": round((t_llm_end - t_llm_start) * 1000, 1),
                "llm_total_ms": round((t_llm_end - t_llm_start) * 1000, 1),
                "e2e_ms": round((t_end - t_start) * 1000, 1),
            },
        }

    def reset(self):
        """Reset session state."""
        self.vad.reset()
        self.session = SessionState()
