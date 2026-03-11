"""Tests for the Socratic state machine."""

import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

import pytest
from socratic.state_machine import (
    SocraticState,
    SocraticStateMachine,
    ResponseCategory,
    TRANSITIONS,
)


class TestSocraticStateMachine:
    """Test state machine initialization and transitions."""

    def test_initial_state_is_opening(self):
        sm = SocraticStateMachine()
        assert sm.state == SocraticState.OPENING

    def test_initial_turn_count_is_zero(self):
        sm = SocraticStateMachine()
        assert sm.turn_count == 0

    def test_initial_history_contains_opening(self):
        sm = SocraticStateMachine()
        assert sm.state_history == [SocraticState.OPENING]

    def test_reset(self):
        sm = SocraticStateMachine()
        sm.transition(ResponseCategory.CORRECT)
        sm.transition(ResponseCategory.CORRECT)
        sm.reset()
        assert sm.state == SocraticState.OPENING
        assert sm.turn_count == 0
        assert sm.state_history == [SocraticState.OPENING]


class TestOpeningTransitions:
    """From OPENING, any response leads to PROBE."""

    @pytest.mark.parametrize("category", list(ResponseCategory))
    def test_opening_always_goes_to_probe(self, category):
        sm = SocraticStateMachine()
        new_state = sm.transition(category)
        assert new_state == SocraticState.PROBE


class TestProbeTransitions:
    """From PROBE, responses branch to different states."""

    def test_correct_goes_to_confirm(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.CONFIRM

    def test_partial_goes_to_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.PARTIALLY_CORRECT) == SocraticState.SCAFFOLD

    def test_incorrect_goes_to_redirect(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.INCORRECT) == SocraticState.REDIRECT

    def test_confused_goes_to_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.CONFUSED) == SocraticState.SCAFFOLD

    def test_off_topic_goes_to_redirect(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.OFF_TOPIC) == SocraticState.REDIRECT

    def test_ack_stays_at_probe(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.ACKNOWLEDGMENT) == SocraticState.PROBE

    def test_deep_insight_goes_to_deepen(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.PROBE
        assert sm.transition(ResponseCategory.DEEP_INSIGHT) == SocraticState.DEEPEN


class TestScaffoldTransitions:
    """From SCAFFOLD, correct → CONFIRM, partial stays, wrong → REDIRECT."""

    def test_correct_goes_to_confirm(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.SCAFFOLD
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.CONFIRM

    def test_partial_stays_at_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.SCAFFOLD
        assert sm.transition(ResponseCategory.PARTIALLY_CORRECT) == SocraticState.SCAFFOLD

    def test_incorrect_goes_to_redirect(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.SCAFFOLD
        assert sm.transition(ResponseCategory.INCORRECT) == SocraticState.REDIRECT


class TestRedirectTransitions:
    """From REDIRECT, correct → CONFIRM, otherwise → SCAFFOLD."""

    def test_correct_goes_to_confirm(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.REDIRECT
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.CONFIRM

    def test_incorrect_goes_to_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.REDIRECT
        assert sm.transition(ResponseCategory.INCORRECT) == SocraticState.SCAFFOLD

    def test_partial_goes_to_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.REDIRECT
        assert sm.transition(ResponseCategory.PARTIALLY_CORRECT) == SocraticState.SCAFFOLD


class TestConfirmTransitions:
    """From CONFIRM, correct → DEEPEN."""

    def test_correct_goes_to_deepen(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.CONFIRM
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.DEEPEN

    def test_ack_goes_to_deepen(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.CONFIRM
        assert sm.transition(ResponseCategory.ACKNOWLEDGMENT) == SocraticState.DEEPEN


class TestDeepenTransitions:
    """From DEEPEN, correct → CLOSE."""

    def test_correct_goes_to_close(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.DEEPEN
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.CLOSE

    def test_deep_insight_goes_to_close(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.DEEPEN
        assert sm.transition(ResponseCategory.DEEP_INSIGHT) == SocraticState.CLOSE

    def test_incorrect_goes_to_redirect(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.DEEPEN
        assert sm.transition(ResponseCategory.INCORRECT) == SocraticState.REDIRECT


class TestCloseTransitions:
    """From CLOSE, mostly stays at CLOSE, but can reopen if needed."""

    def test_correct_stays_at_close(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.CLOSE
        assert sm.transition(ResponseCategory.CORRECT) == SocraticState.CLOSE

    def test_confused_goes_to_scaffold(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.CLOSE
        assert sm.transition(ResponseCategory.CONFUSED) == SocraticState.SCAFFOLD

    def test_incorrect_goes_to_redirect(self):
        sm = SocraticStateMachine()
        sm.state = SocraticState.CLOSE
        assert sm.transition(ResponseCategory.INCORRECT) == SocraticState.REDIRECT


class TestFullConversationFlow:
    """Test realistic multi-turn conversation flows."""

    def test_ideal_flow_opening_to_close(self):
        """Student gets everything right: OPENING→PROBE→CONFIRM→DEEPEN→CLOSE."""
        sm = SocraticStateMachine()
        assert sm.state == SocraticState.OPENING

        sm.transition(ResponseCategory.ACKNOWLEDGMENT)  # Student says "hi"
        assert sm.state == SocraticState.PROBE

        sm.transition(ResponseCategory.CORRECT)  # Student answers correctly
        assert sm.state == SocraticState.CONFIRM

        sm.transition(ResponseCategory.CORRECT)  # Student explains why
        assert sm.state == SocraticState.DEEPEN

        sm.transition(ResponseCategory.CORRECT)  # Student handles deeper question
        assert sm.state == SocraticState.CLOSE

    def test_struggling_student_flow(self):
        """Student struggles: OPENING→PROBE→REDIRECT→SCAFFOLD→CONFIRM."""
        sm = SocraticStateMachine()

        sm.transition(ResponseCategory.ACKNOWLEDGMENT)  # "ok"
        assert sm.state == SocraticState.PROBE

        sm.transition(ResponseCategory.INCORRECT)  # wrong answer
        assert sm.state == SocraticState.REDIRECT

        sm.transition(ResponseCategory.PARTIALLY_CORRECT)  # getting closer
        assert sm.state == SocraticState.SCAFFOLD

        sm.transition(ResponseCategory.CORRECT)  # got it!
        assert sm.state == SocraticState.CONFIRM

    def test_state_history_tracks_all_transitions(self):
        sm = SocraticStateMachine()
        sm.transition(ResponseCategory.ACKNOWLEDGMENT)
        sm.transition(ResponseCategory.INCORRECT)
        sm.transition(ResponseCategory.CORRECT)

        assert sm.state_history == [
            SocraticState.OPENING,
            SocraticState.PROBE,
            SocraticState.REDIRECT,
            SocraticState.CONFIRM,
        ]
        assert sm.turn_count == 3

    def test_turn_count_increments(self):
        sm = SocraticStateMachine()
        for _ in range(5):
            sm.transition(ResponseCategory.ACKNOWLEDGMENT)
        assert sm.turn_count == 5


class TestTransitionTableCompleteness:
    """Verify every (state, category) pair has a defined transition."""

    @pytest.mark.parametrize("state", list(SocraticState))
    @pytest.mark.parametrize("category", list(ResponseCategory))
    def test_all_transitions_defined(self, state, category):
        key = (state, category)
        assert key in TRANSITIONS, f"Missing transition for {state.value} + {category.value}"
