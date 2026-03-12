"""Tests for the cost tracker module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

import pytest
from instrumentation.cost_tracker import CostTracker, TurnCost, PRICING


class TestTurnCost:
    def test_to_dict(self):
        tc = TurnCost(turn_id=1, stt_cost=0.001, llm_cost=0.002, tts_cost=0.0005, total_cost=0.0035, model_used="groq")
        d = tc.to_dict()
        assert d["turn_id"] == 1
        assert d["total_cost"] == 0.0035
        assert d["model_used"] == "groq"


class TestCostTracker:
    def setup_method(self):
        self.tracker = CostTracker()

    def test_initial_state(self):
        assert self.tracker.total_session_cost == 0.0
        assert len(self.tracker.turns) == 0

    def test_groq_llm_cost(self):
        cost = self.tracker.calculate_turn_cost(
            turn_id=1,
            model="groq",
            input_tokens=500,
            output_tokens=200,
        )
        expected_input = (500 / 1_000_000) * PRICING["groq"]["input_per_1m"]
        expected_output = (200 / 1_000_000) * PRICING["groq"]["output_per_1m"]
        assert abs(cost.llm_cost - (expected_input + expected_output)) < 1e-9

    def test_claude_llm_cost(self):
        cost = self.tracker.calculate_turn_cost(
            turn_id=1,
            model="claude",
            input_tokens=1000,
            output_tokens=500,
        )
        expected_input = (1000 / 1_000_000) * PRICING["claude"]["input_per_1m"]
        expected_output = (500 / 1_000_000) * PRICING["claude"]["output_per_1m"]
        assert abs(cost.llm_cost - (expected_input + expected_output)) < 1e-9

    def test_claude_more_expensive_than_groq(self):
        groq_cost = self.tracker.calculate_turn_cost(
            turn_id=1, model="groq", input_tokens=1000, output_tokens=500,
        )
        claude_cost = self.tracker.calculate_turn_cost(
            turn_id=2, model="claude", input_tokens=1000, output_tokens=500,
        )
        assert claude_cost.llm_cost > groq_cost.llm_cost

    def test_stt_cost(self):
        cost = self.tracker.calculate_turn_cost(
            turn_id=1, model="groq", audio_seconds=5.0,
        )
        expected = 5.0 * PRICING["assemblyai"]["per_audio_second"]
        assert abs(cost.stt_cost - expected) < 1e-9

    def test_tts_cost(self):
        cost = self.tracker.calculate_turn_cost(
            turn_id=1, model="groq", tts_characters=500,
        )
        expected = 500 * PRICING["elevenlabs"]["per_character"]
        assert abs(cost.tts_cost - expected) < 1e-9

    def test_total_cost_is_sum(self):
        cost = self.tracker.calculate_turn_cost(
            turn_id=1,
            model="groq",
            input_tokens=1000,
            output_tokens=200,
            audio_seconds=3.0,
            tts_characters=300,
        )
        assert abs(cost.total_cost - (cost.stt_cost + cost.llm_cost + cost.tts_cost)) < 1e-9

    def test_session_accumulates(self):
        self.tracker.calculate_turn_cost(turn_id=1, model="groq", input_tokens=1000, output_tokens=200)
        self.tracker.calculate_turn_cost(turn_id=2, model="claude", input_tokens=1000, output_tokens=200)
        assert len(self.tracker.turns) == 2
        assert self.tracker.total_session_cost > 0

    def test_session_summary(self):
        self.tracker.calculate_turn_cost(turn_id=1, model="groq", input_tokens=1000, output_tokens=200)
        self.tracker.calculate_turn_cost(turn_id=2, model="groq", input_tokens=1000, output_tokens=200)
        summary = self.tracker.session_summary()
        assert summary["total_turns"] == 2
        assert summary["total_cost"] > 0
        assert summary["avg_cost_per_turn"] > 0
        assert "stt_total" in summary["breakdown"]
        assert "llm_total" in summary["breakdown"]
        assert "tts_total" in summary["breakdown"]

    def test_reset(self):
        self.tracker.calculate_turn_cost(turn_id=1, model="groq", input_tokens=1000, output_tokens=200)
        self.tracker.reset()
        assert self.tracker.total_session_cost == 0.0
        assert len(self.tracker.turns) == 0

    def test_unknown_model_zero_llm_cost(self):
        cost = self.tracker.calculate_turn_cost(turn_id=1, model="unknown", input_tokens=1000, output_tokens=200)
        assert cost.llm_cost == 0.0

    def test_zero_tokens_zero_cost(self):
        cost = self.tracker.calculate_turn_cost(turn_id=1, model="groq")
        assert cost.llm_cost == 0.0
        assert cost.stt_cost == 0.0
        assert cost.tts_cost == 0.0
        assert cost.total_cost == 0.0

    def test_empty_session_summary(self):
        summary = self.tracker.session_summary()
        assert summary["total_turns"] == 0
        assert summary["total_cost"] == 0
        assert summary["avg_cost_per_turn"] == 0
