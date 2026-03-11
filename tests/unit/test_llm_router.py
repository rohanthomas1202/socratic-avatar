"""Tests for the LLM router and classifier."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

import pytest
from socratic.state_machine import SocraticState
from socratic.classifier import (
    classify_response,
    ResponseCategory,
    get_concept_keywords,
    get_expected_ideas,
)
from pipeline.llm_router import LLMRouter, QUALITY_STATES, FAST_STATES


class TestClassifier:
    """Test the rule-based response classifier."""

    def test_empty_string_is_ack(self):
        assert classify_response("") == ResponseCategory.ACKNOWLEDGMENT

    @pytest.mark.parametrize("text", [
        "ok", "okay", "sure", "yes", "yeah", "yep", "got it",
        "i see", "alright", "right", "mhm", "cool",
    ])
    def test_short_acks(self, text):
        assert classify_response(text) == ResponseCategory.ACKNOWLEDGMENT

    @pytest.mark.parametrize("text", [
        "I don't know",
        "I'm confused",
        "Can you explain?",
        "I have no idea",
        "help",
        "not sure",
        "idk",
    ])
    def test_confused_responses(self, text):
        assert classify_response(text) == ResponseCategory.CONFUSED

    def test_deep_insight_requires_length_and_indicators(self):
        text = "Because if you divide by zero, that implies the inverse would mean zero times something equals the original, which connects to the fundamental property of multiplication"
        result = classify_response(text)
        assert result == ResponseCategory.DEEP_INSIGHT

    def test_short_deep_indicator_is_not_deep(self):
        # Only one indicator and short — should not be DEEP_INSIGHT
        text = "because yes"
        result = classify_response(text)
        assert result != ResponseCategory.DEEP_INSIGHT

    def test_off_topic_with_keywords(self):
        keywords = ["divide", "zero", "multiplication"]
        text = "I really like playing basketball with my friends after school"
        result = classify_response(text, concept_keywords=keywords)
        assert result == ResponseCategory.OFF_TOPIC

    def test_on_topic_not_off_topic(self):
        keywords = ["divide", "zero", "multiplication"]
        text = "When you divide something by zero it breaks"
        result = classify_response(text, concept_keywords=keywords)
        assert result != ResponseCategory.OFF_TOPIC

    def test_correct_with_expected_ideas(self):
        ideas = ["undefined", "multiply by zero", "inverse"]
        text = "Division by zero is undefined because multiply by zero always gives zero"
        result = classify_response(text, expected_ideas=ideas)
        assert result == ResponseCategory.CORRECT

    def test_partial_with_one_idea(self):
        ideas = ["undefined", "multiply by zero", "inverse"]
        text = "I think it's undefined but I'm not sure why"
        result = classify_response(text, expected_ideas=ideas)
        assert result == ResponseCategory.PARTIALLY_CORRECT

    def test_very_short_answer_is_ack(self):
        text = "yes it is"
        result = classify_response(text)
        assert result == ResponseCategory.ACKNOWLEDGMENT

    def test_medium_answer_without_ideas_is_partial(self):
        text = "I think the answer has something to do with numbers"
        result = classify_response(text)
        assert result == ResponseCategory.PARTIALLY_CORRECT


class TestConceptKeywords:
    """Test keyword lookup for concepts."""

    def test_division_by_zero_has_keywords(self):
        kw = get_concept_keywords("division_by_zero")
        assert "divide" in kw
        assert "zero" in kw

    def test_photosynthesis_has_keywords(self):
        kw = get_concept_keywords("photosynthesis")
        assert "plant" in kw
        assert "sun" in kw

    def test_unknown_concept_returns_empty(self):
        kw = get_concept_keywords("quantum_physics")
        assert kw == []


class TestExpectedIdeas:
    """Test expected ideas lookup."""

    def test_division_by_zero_ideas(self):
        ideas = get_expected_ideas("division_by_zero")
        assert "undefined" in ideas

    def test_unknown_concept_returns_empty(self):
        ideas = get_expected_ideas("quantum_physics")
        assert ideas == []


class TestLLMRouterSelection:
    """Test model selection based on Socratic state."""

    def setup_method(self):
        self.router = LLMRouter()

    def test_opening_uses_groq(self):
        assert self.router.select_model(SocraticState.OPENING) == "groq"

    def test_confirm_uses_groq(self):
        assert self.router.select_model(SocraticState.CONFIRM) == "groq"

    def test_close_uses_groq(self):
        assert self.router.select_model(SocraticState.CLOSE) == "groq"

    def test_scaffold_uses_claude(self):
        assert self.router.select_model(SocraticState.SCAFFOLD) == "claude"

    def test_redirect_uses_claude(self):
        assert self.router.select_model(SocraticState.REDIRECT) == "claude"

    def test_deepen_uses_claude(self):
        assert self.router.select_model(SocraticState.DEEPEN) == "claude"

    def test_probe_uses_claude(self):
        assert self.router.select_model(SocraticState.PROBE) == "claude"

    def test_all_states_covered(self):
        """Every state should be in either QUALITY_STATES or FAST_STATES."""
        for state in SocraticState:
            assert state in QUALITY_STATES or state in FAST_STATES, \
                f"{state.value} not in either routing set"
