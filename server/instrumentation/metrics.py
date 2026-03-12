"""Session-level metrics aggregation: mean, p50, p95, p99, variance."""

import math
from dataclasses import dataclass, field


@dataclass
class MetricsAggregator:
    """Accumulates per-turn metrics and computes session-level statistics."""

    _values: dict[str, list[float]] = field(default_factory=dict)
    turn_count: int = 0

    def record_turn(self, metrics: dict) -> None:
        """Record a turn's metrics. Expects keys like stt_ms, llm_ttft_ms, etc."""
        self.turn_count += 1
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key != "turn_id":
                if key not in self._values:
                    self._values[key] = []
                self._values[key].append(float(value))

    def get_stats(self, key: str) -> dict:
        """Get aggregated stats for a single metric key."""
        values = self._values.get(key, [])
        if not values:
            return {"mean": 0, "p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "variance": 0, "count": 0}

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        return {
            "mean": round(_mean(sorted_vals), 1),
            "p50": round(_percentile(sorted_vals, 50), 1),
            "p95": round(_percentile(sorted_vals, 95), 1),
            "p99": round(_percentile(sorted_vals, 99), 1),
            "min": round(sorted_vals[0], 1),
            "max": round(sorted_vals[-1], 1),
            "variance": round(_variance(sorted_vals), 1),
            "count": n,
        }

    def summary(self) -> dict:
        """Get aggregated stats for all tracked metrics."""
        result = {"turn_count": self.turn_count}
        for key in self._values:
            result[key] = self.get_stats(key)
        return result

    def last_turn(self) -> dict:
        """Get the most recent value for each metric."""
        return {
            key: round(values[-1], 1) if values else 0
            for key, values in self._values.items()
        }

    def reset(self) -> None:
        """Clear all accumulated metrics."""
        self._values.clear()
        self.turn_count = 0


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    return sum((v - avg) ** 2 for v in values) / (len(values) - 1)


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Calculate percentile from pre-sorted values using nearest-rank method."""
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    rank = (pct / 100) * (n - 1)
    lower = int(math.floor(rank))
    upper = min(lower + 1, n - 1)
    frac = rank - lower
    return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])
