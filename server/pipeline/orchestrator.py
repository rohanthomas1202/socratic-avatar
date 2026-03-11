"""Pipeline orchestrator — manages the turn lifecycle.

Coordinates all pipeline stages for a single conversational turn:
1. Receive audio chunks from client
2. Feed to VAD → detect speech end
3. Transcribe with STT
4. Classify response → transition state machine → build prompt → route LLM
5. Stream LLM tokens → sentence chunker → TTS → audio out
6. Emit per-stage metrics
"""

import logging
import time
from dataclasses import dataclass, field

from pipeline.vad import VoiceActivityDetector
from pipeline.stt import AssemblyAISTT
from pipeline.llm_router import LLMRouter
from pipeline.sentence_chunker import SentenceChunker
from pipeline.tts import ElevenLabsTTS
from socratic.state_machine import SocraticStateMachine, SocraticState
from socratic.classifier import (
    classify_response,
    get_concept_keywords,
    get_expected_ideas,
)
from socratic.concepts import get_concept, ConceptDefinition
from socratic.prompts import get_system_prompt

logger = logging.getLogger(__name__)


@dataclass
class TurnMetrics:
    """Latency metrics for a single conversational turn."""
    turn_id: int = 0
    vad_end_ms: float = 0.0
    stt_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_total_ms: float = 0.0
    tts_first_ms: float = 0.0
    e2e_ms: float = 0.0


@dataclass
class SessionState:
    """State for an active tutoring session."""
    turn_count: int = 0
    conversation_history: list[dict] = field(default_factory=list)
    is_active: bool = True


class PipelineOrchestrator:
    """Coordinates the streaming pipeline for a tutoring session."""

    def __init__(self, concept_id: str | None = None):
        self.vad = VoiceActivityDetector()
        self.stt = AssemblyAISTT()
        self.router = LLMRouter()
        self.chunker = SentenceChunker()
        self.tts = ElevenLabsTTS()
        self.session = SessionState()
        self.state_machine = SocraticStateMachine()

        # Load concept
        self.concept: ConceptDefinition | None = None
        if concept_id:
            self.concept = get_concept(concept_id)
        if not self.concept:
            self.concept = get_concept("division_by_zero")

        self.concept_keywords = get_concept_keywords(self.concept.id) if self.concept else []
        self.expected_ideas = get_expected_ideas(self.concept.id) if self.concept else []

    @property
    def current_state(self) -> SocraticState:
        return self.state_machine.state

    def _get_system_prompt(self) -> str:
        """Build the system prompt for the current state and concept."""
        if not self.concept:
            return "You are a helpful Socratic tutor."
        return get_system_prompt(
            state=self.state_machine.state,
            concept_name=self.concept.name,
            concept_context=self.concept.context,
        )

    def process_audio_chunk(self, audio_bytes: bytes) -> dict:
        """Process an incoming audio chunk through VAD."""
        return self.vad.process_chunk(audio_bytes)

    async def process_turn(self, audio_bytes: bytes) -> dict:
        """Process a complete turn: audio → STT → classify → route LLM → response.

        Non-streaming version for simple request/response.
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

        # Classify and transition state
        category = classify_response(
            transcript,
            concept_keywords=self.concept_keywords,
            expected_ideas=self.expected_ideas,
        )
        new_state = self.state_machine.transition(category)
        model_name = self.router.select_model(self.state_machine.state)
        logger.info(f"Turn {turn_id}: classified={category.value}, state→{new_state.value}")

        # LLM with state-specific prompt
        system_prompt = self._get_system_prompt()
        t_llm_start = time.perf_counter()
        response = await self.router.generate(
            user_message=transcript,
            conversation_history=self.session.conversation_history,
            system_prompt=system_prompt,
            state=self.state_machine.state,
        )
        t_llm_end = time.perf_counter()

        self._update_history(transcript, response)

        t_end = time.perf_counter()

        metrics = TurnMetrics(
            turn_id=turn_id,
            stt_ms=(t_stt_end - t_stt_start) * 1000,
            llm_ttft_ms=(t_llm_end - t_llm_start) * 1000,
            llm_total_ms=(t_llm_end - t_llm_start) * 1000,
            e2e_ms=(t_end - t_start) * 1000,
        )

        return {
            "turn_id": turn_id,
            "transcript": transcript,
            "response": response,
            "socratic_state": new_state.value,
            "model": model_name,
            "metrics": {
                "turn_id": metrics.turn_id,
                "stt_ms": round(metrics.stt_ms, 1),
                "llm_ttft_ms": round(metrics.llm_ttft_ms, 1),
                "e2e_ms": round(metrics.e2e_ms, 1),
            },
        }

    async def process_turn_streaming(self, audio_bytes: bytes):
        """Process a turn with full streaming: STT → classify → route LLM → TTS.

        Yields events as they occur.
        """
        self.session.turn_count += 1
        turn_id = self.session.turn_count
        t_start = time.perf_counter()

        # --- STT ---
        t_stt_start = time.perf_counter()
        transcript = await self.stt.transcribe_audio(audio_bytes)
        t_stt_end = time.perf_counter()

        if not transcript.strip():
            yield {"type": "turn_empty", "turn_id": turn_id}
            return

        # --- Classify and transition ---
        category = classify_response(
            transcript,
            concept_keywords=self.concept_keywords,
            expected_ideas=self.expected_ideas,
        )
        new_state = self.state_machine.transition(category)
        model_name = self.router.select_model(self.state_machine.state)
        logger.info(
            f"Turn {turn_id}: classified={category.value}, "
            f"state→{new_state.value}, model={model_name}"
        )

        yield {
            "type": "transcript",
            "turn_id": turn_id,
            "text": transcript,
            "stt_ms": round((t_stt_end - t_stt_start) * 1000, 1),
            "socratic_state": new_state.value,
            "model": model_name,
        }

        # --- Stream LLM tokens → sentence chunker → TTS ---
        system_prompt = self._get_system_prompt()
        t_llm_start = time.perf_counter()
        first_token = True
        first_tts_byte = True
        t_tts_first = None
        full_response = []
        self.chunker.reset()

        async for token in self.router.generate_stream(
            user_message=transcript,
            conversation_history=self.session.conversation_history,
            system_prompt=system_prompt,
            state=self.state_machine.state,
        ):
            if first_token:
                ttft = (time.perf_counter() - t_llm_start) * 1000
                yield {"type": "llm_ttft", "turn_id": turn_id, "ttft_ms": round(ttft, 1)}
                first_token = False

            full_response.append(token)
            yield {"type": "token", "turn_id": turn_id, "text": token}

            sentence = self.chunker.add_token(token)
            if sentence:
                yield {"type": "sentence", "turn_id": turn_id, "text": sentence}
                async for audio_chunk in self.tts.synthesize_streaming(sentence):
                    if first_tts_byte:
                        t_tts_first = time.perf_counter()
                        first_tts_byte = False
                    yield {"type": "audio", "turn_id": turn_id, "data": audio_chunk}

        t_llm_end = time.perf_counter()

        # Flush remaining text from chunker
        remaining = self.chunker.flush()
        if remaining:
            yield {"type": "sentence", "turn_id": turn_id, "text": remaining}
            async for audio_chunk in self.tts.synthesize_streaming(remaining):
                if first_tts_byte:
                    t_tts_first = time.perf_counter()
                    first_tts_byte = False
                yield {"type": "audio", "turn_id": turn_id, "data": audio_chunk}

        response_text = "".join(full_response)
        self._update_history(transcript, response_text)

        t_end = time.perf_counter()

        tts_first_ms = 0.0
        if t_tts_first is not None:
            tts_first_ms = (t_tts_first - t_stt_end) * 1000

        yield {
            "type": "turn_complete",
            "turn_id": turn_id,
            "text": response_text,
            "socratic_state": new_state.value,
            "model": model_name,
            "metrics": {
                "stt_ms": round((t_stt_end - t_stt_start) * 1000, 1),
                "llm_ttft_ms": round(ttft if not first_token else 0, 1),
                "llm_total_ms": round((t_llm_end - t_llm_start) * 1000, 1),
                "tts_first_ms": round(tts_first_ms, 1),
                "e2e_ms": round((t_end - t_start) * 1000, 1),
            },
        }

    async def process_text_turn_streaming(self, text: str):
        """Process a text-input turn with full streaming pipeline.

        Same as process_turn_streaming but skips STT.
        """
        self.session.turn_count += 1
        turn_id = self.session.turn_count
        t_start = time.perf_counter()

        # --- Classify and transition ---
        category = classify_response(
            text,
            concept_keywords=self.concept_keywords,
            expected_ideas=self.expected_ideas,
        )
        new_state = self.state_machine.transition(category)
        model_name = self.router.select_model(self.state_machine.state)
        logger.info(
            f"Turn {turn_id} (text): classified={category.value}, "
            f"state→{new_state.value}, model={model_name}"
        )

        yield {
            "type": "transcript",
            "turn_id": turn_id,
            "text": text,
            "stt_ms": 0,
            "socratic_state": new_state.value,
            "model": model_name,
        }

        # --- Stream LLM → Chunker → TTS ---
        system_prompt = self._get_system_prompt()
        t_llm_start = time.perf_counter()
        first_token = True
        first_tts = True
        ttft_ms = 0.0
        tts_first_ms = 0.0
        full_response = []
        self.chunker.reset()

        async for token in self.router.generate_stream(
            user_message=text,
            conversation_history=self.session.conversation_history,
            system_prompt=system_prompt,
            state=self.state_machine.state,
        ):
            if first_token:
                ttft_ms = (time.perf_counter() - t_llm_start) * 1000
                yield {"type": "llm_ttft", "turn_id": turn_id, "ttft_ms": round(ttft_ms, 1)}
                first_token = False

            full_response.append(token)
            yield {"type": "token", "turn_id": turn_id, "text": token}

            sentence = self.chunker.add_token(token)
            if sentence:
                yield {"type": "sentence", "turn_id": turn_id, "text": sentence}
                async for audio_chunk in self.tts.synthesize_streaming(sentence):
                    if first_tts:
                        tts_first_ms = (time.perf_counter() - t_llm_start) * 1000
                        first_tts = False
                    yield {"type": "audio", "turn_id": turn_id, "data": audio_chunk}

        t_llm_end = time.perf_counter()

        remaining = self.chunker.flush()
        if remaining:
            yield {"type": "sentence", "turn_id": turn_id, "text": remaining}
            async for audio_chunk in self.tts.synthesize_streaming(remaining):
                if first_tts:
                    tts_first_ms = (time.perf_counter() - t_llm_start) * 1000
                    first_tts = False
                yield {"type": "audio", "turn_id": turn_id, "data": audio_chunk}

        response_text = "".join(full_response)
        self._update_history(text, response_text)

        t_end = time.perf_counter()

        yield {
            "type": "turn_complete",
            "turn_id": turn_id,
            "text": response_text,
            "socratic_state": new_state.value,
            "model": model_name,
            "metrics": {
                "stt_ms": 0,
                "llm_ttft_ms": round(ttft_ms, 1),
                "llm_total_ms": round((t_llm_end - t_llm_start) * 1000, 1),
                "tts_first_ms": round(tts_first_ms, 1),
                "e2e_ms": round((t_end - t_start) * 1000, 1),
            },
        }

    def _update_history(self, user_text: str, assistant_text: str):
        """Update conversation history, keeping last 20 messages."""
        self.session.conversation_history.append({"role": "user", "content": user_text})
        self.session.conversation_history.append({"role": "assistant", "content": assistant_text})
        if len(self.session.conversation_history) > 20:
            self.session.conversation_history = self.session.conversation_history[-20:]

    def reset(self):
        """Reset session state."""
        self.vad.reset()
        self.chunker.reset()
        self.session = SessionState()
        self.state_machine.reset()
