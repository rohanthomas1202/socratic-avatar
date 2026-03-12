"""Per-turn API cost calculation based on token counts and pricing."""

from dataclasses import dataclass, field

# Pricing per 1M tokens (input/output) as of 2025
PRICING = {
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "input_per_1m": 0.59,
        "output_per_1m": 0.79,
    },
    "claude": {
        "model": "claude-sonnet-4-6",
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
    },
    # STT: AssemblyAI charges per audio-second
    "assemblyai": {
        "per_audio_second": 0.00025,  # ~$0.015/min
    },
    # TTS: ElevenLabs charges per character
    "elevenlabs": {
        "per_character": 0.00003,  # ~$0.30 per 10k chars
    },
}


@dataclass
class TurnCost:
    """Cost breakdown for a single turn."""
    turn_id: int = 0
    stt_cost: float = 0.0
    llm_cost: float = 0.0
    tts_cost: float = 0.0
    total_cost: float = 0.0
    model_used: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "stt_cost": round(self.stt_cost, 6),
            "llm_cost": round(self.llm_cost, 6),
            "tts_cost": round(self.tts_cost, 6),
            "total_cost": round(self.total_cost, 6),
            "model_used": self.model_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class CostTracker:
    """Tracks API costs across a tutoring session."""

    turns: list[TurnCost] = field(default_factory=list)
    total_session_cost: float = 0.0

    def calculate_turn_cost(
        self,
        turn_id: int,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_seconds: float = 0.0,
        tts_characters: int = 0,
    ) -> TurnCost:
        """Calculate cost for a single turn."""
        # LLM cost
        llm_cost = 0.0
        pricing = PRICING.get(model, {})
        if "input_per_1m" in pricing:
            llm_cost = (
                (input_tokens / 1_000_000) * pricing["input_per_1m"]
                + (output_tokens / 1_000_000) * pricing["output_per_1m"]
            )

        # STT cost
        stt_cost = audio_seconds * PRICING["assemblyai"]["per_audio_second"]

        # TTS cost
        tts_cost = tts_characters * PRICING["elevenlabs"]["per_character"]

        total = stt_cost + llm_cost + tts_cost

        turn_cost = TurnCost(
            turn_id=turn_id,
            stt_cost=stt_cost,
            llm_cost=llm_cost,
            tts_cost=tts_cost,
            total_cost=total,
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        self.turns.append(turn_cost)
        self.total_session_cost += total

        return turn_cost

    def session_summary(self) -> dict:
        """Get session cost summary."""
        return {
            "total_turns": len(self.turns),
            "total_cost": round(self.total_session_cost, 6),
            "avg_cost_per_turn": round(
                self.total_session_cost / len(self.turns), 6
            ) if self.turns else 0,
            "breakdown": {
                "stt_total": round(sum(t.stt_cost for t in self.turns), 6),
                "llm_total": round(sum(t.llm_cost for t in self.turns), 6),
                "tts_total": round(sum(t.tts_cost for t in self.turns), 6),
            },
        }

    def reset(self) -> None:
        self.turns.clear()
        self.total_session_cost = 0.0
