"""Tests for the metrics aggregation module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

import pytest
from instrumentation.metrics import MetricsAggregator, _mean, _variance, _percentile
from instrumentation.timer import TurnTimer


class TestMean:
    def test_empty(self):
        assert _mean([]) == 0.0

    def test_single(self):
        assert _mean([5.0]) == 5.0

    def test_multiple(self):
        assert _mean([1.0, 2.0, 3.0]) == 2.0

    def test_decimals(self):
        assert abs(_mean([1.5, 2.5]) - 2.0) < 0.001


class TestVariance:
    def test_empty(self):
        assert _variance([]) == 0.0

    def test_single(self):
        assert _variance([5.0]) == 0.0

    def test_identical(self):
        assert _variance([3.0, 3.0, 3.0]) == 0.0

    def test_sample_variance(self):
        # [1, 2, 3] → mean=2, sample variance = ((1+0+1) / 2) = 1.0
        assert _variance([1.0, 2.0, 3.0]) == 1.0

    def test_spread(self):
        result = _variance([10.0, 20.0, 30.0, 40.0])
        # mean=25, deviations: -15, -5, 5, 15, sum_sq=500, var=500/3≈166.67
        assert abs(result - 166.667) < 0.1


class TestPercentile:
    def test_empty(self):
        assert _percentile([], 50) == 0.0

    def test_single(self):
        assert _percentile([42.0], 50) == 42.0
        assert _percentile([42.0], 95) == 42.0

    def test_median_odd(self):
        assert _percentile([1.0, 2.0, 3.0], 50) == 2.0

    def test_median_even(self):
        result = _percentile([1.0, 2.0, 3.0, 4.0], 50)
        assert result == 2.5

    def test_p95_small(self):
        vals = sorted([100.0, 200.0, 300.0, 400.0, 500.0])
        result = _percentile(vals, 95)
        # rank = 0.95 * 4 = 3.8, interp between 400 and 500 → 480
        assert abs(result - 480.0) < 0.1

    def test_p99(self):
        vals = list(range(1, 101))  # 1 to 100
        result = _percentile([float(v) for v in vals], 99)
        assert result >= 99.0

    def test_p0_is_min(self):
        assert _percentile([5.0, 10.0, 15.0], 0) == 5.0

    def test_p100_is_max(self):
        assert _percentile([5.0, 10.0, 15.0], 100) == 15.0


class TestMetricsAggregator:
    def test_initial_state(self):
        agg = MetricsAggregator()
        assert agg.turn_count == 0
        assert agg.summary() == {"turn_count": 0}

    def test_record_single_turn(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 150.0, "llm_ttft_ms": 200.0, "e2e_ms": 800.0})
        assert agg.turn_count == 1
        stats = agg.get_stats("stt_ms")
        assert stats["mean"] == 150.0
        assert stats["count"] == 1

    def test_record_multiple_turns(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 100.0, "e2e_ms": 500.0})
        agg.record_turn({"stt_ms": 200.0, "e2e_ms": 700.0})
        agg.record_turn({"stt_ms": 300.0, "e2e_ms": 900.0})
        assert agg.turn_count == 3

        stats = agg.get_stats("stt_ms")
        assert stats["mean"] == 200.0
        assert stats["p50"] == 200.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["count"] == 3

    def test_ignores_turn_id(self):
        agg = MetricsAggregator()
        agg.record_turn({"turn_id": 1, "stt_ms": 100.0})
        assert "turn_id" not in agg._values

    def test_ignores_non_numeric(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 100.0, "model": "groq"})
        assert "model" not in agg._values

    def test_last_turn(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 100.0})
        agg.record_turn({"stt_ms": 200.0})
        last = agg.last_turn()
        assert last["stt_ms"] == 200.0

    def test_summary_includes_all_keys(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 100.0, "llm_ttft_ms": 50.0, "e2e_ms": 500.0})
        summary = agg.summary()
        assert "stt_ms" in summary
        assert "llm_ttft_ms" in summary
        assert "e2e_ms" in summary
        assert summary["turn_count"] == 1

    def test_reset(self):
        agg = MetricsAggregator()
        agg.record_turn({"stt_ms": 100.0})
        agg.reset()
        assert agg.turn_count == 0
        assert agg.summary() == {"turn_count": 0}

    def test_unknown_key_stats(self):
        agg = MetricsAggregator()
        stats = agg.get_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["mean"] == 0


class TestTurnTimer:
    def test_mark_and_elapsed(self):
        timer = TurnTimer(turn_id=1)
        timer.mark("a")
        # Simulate some time
        timer._marks["b"] = timer._marks["a"] + 0.150  # 150ms
        elapsed = timer.elapsed_ms("a", "b")
        assert abs(elapsed - 150.0) < 0.1

    def test_elapsed_missing_mark(self):
        timer = TurnTimer(turn_id=1)
        timer.mark("a")
        assert timer.elapsed_ms("a", "nonexistent") == 0.0
        assert timer.elapsed_ms("nonexistent", "a") == 0.0

    def test_get_mark(self):
        timer = TurnTimer(turn_id=1)
        ts = timer.mark("test")
        assert timer.get("test") == ts
        assert timer.get("missing") is None

    def test_to_dict(self):
        timer = TurnTimer(turn_id=1)
        timer.mark("a")
        timer.mark("b")
        d = timer.to_dict()
        assert "a" in d
        assert "b" in d

    def test_summary(self):
        timer = TurnTimer(turn_id=5)
        timer.mark("turn_start")
        timer._marks["stt_start"] = timer._marks["turn_start"] + 0.0
        timer._marks["stt_end"] = timer._marks["turn_start"] + 0.200
        timer._marks["llm_start"] = timer._marks["stt_end"]
        timer._marks["llm_first_token"] = timer._marks["llm_start"] + 0.150
        timer._marks["tts_first_byte"] = timer._marks["llm_start"] + 0.300
        timer._marks["llm_end"] = timer._marks["llm_start"] + 0.500
        timer._marks["turn_end"] = timer._marks["turn_start"] + 0.900

        s = timer.summary()
        assert s["turn_id"] == 5
        assert abs(s["stt_ms"] - 200.0) < 0.1
        assert abs(s["llm_ttft_ms"] - 150.0) < 0.1
        assert abs(s["llm_total_ms"] - 500.0) < 0.1
        assert abs(s["tts_first_ms"] - 300.0) < 0.1
        assert abs(s["e2e_ms"] - 900.0) < 0.1
