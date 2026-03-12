"""Per-stage timestamp collection for pipeline turns."""

import time
from dataclasses import dataclass, field


@dataclass
class TurnTimer:
    """Collects per-stage timestamps for a single pipeline turn.

    Usage:
        timer = TurnTimer(turn_id=1)
        timer.mark("stt_start")
        ...
        timer.mark("stt_end")
        timer.mark("llm_start")
        ...
        stt_ms = timer.elapsed_ms("stt_start", "stt_end")
    """

    turn_id: int = 0
    _marks: dict[str, float] = field(default_factory=dict)

    def mark(self, name: str) -> float:
        """Record a timestamp with the given name. Returns the timestamp."""
        ts = time.perf_counter()
        self._marks[name] = ts
        return ts

    def get(self, name: str) -> float | None:
        """Get a recorded timestamp by name."""
        return self._marks.get(name)

    def elapsed_ms(self, start: str, end: str) -> float:
        """Calculate milliseconds between two marks. Returns 0 if either is missing."""
        t_start = self._marks.get(start)
        t_end = self._marks.get(end)
        if t_start is None or t_end is None:
            return 0.0
        return (t_end - t_start) * 1000

    def to_dict(self) -> dict:
        """Export all marks as {name: timestamp_seconds}."""
        return dict(self._marks)

    def summary(self) -> dict:
        """Compute standard pipeline metrics from marks."""
        return {
            "turn_id": self.turn_id,
            "stt_ms": round(self.elapsed_ms("stt_start", "stt_end"), 1),
            "llm_ttft_ms": round(self.elapsed_ms("llm_start", "llm_first_token"), 1),
            "llm_total_ms": round(self.elapsed_ms("llm_start", "llm_end"), 1),
            "tts_first_ms": round(self.elapsed_ms("llm_start", "tts_first_byte"), 1),
            "e2e_ms": round(self.elapsed_ms("turn_start", "turn_end"), 1),
        }
