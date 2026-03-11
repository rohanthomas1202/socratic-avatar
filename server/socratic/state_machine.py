"""Socratic tutoring state machine.

Seven states model the pedagogical flow of a Socratic tutoring session:
OPENING → PROBE → SCAFFOLD/REDIRECT/CONFIRM → DEEPEN → CLOSE

Transitions are driven by the classifier's assessment of student responses.
"""

from enum import Enum


class SocraticState(str, Enum):
    """States in the Socratic tutoring conversation."""
    OPENING = "opening"      # Greet, introduce concept, spark curiosity
    PROBE = "probe"          # Ask diagnostic question to gauge understanding
    SCAFFOLD = "scaffold"    # Guide with leading questions (student partially correct)
    REDIRECT = "redirect"    # Student is wrong — ask revealing question to expose error
    CONFIRM = "confirm"      # Student is right — ask them to explain WHY
    DEEPEN = "deepen"        # Push beyond surface understanding
    CLOSE = "close"          # Summarize through questions, wrap up


class ResponseCategory(str, Enum):
    """How the classifier categorizes a student's response."""
    CORRECT = "correct"          # Student demonstrates understanding
    PARTIALLY_CORRECT = "partial"  # On the right track but incomplete
    INCORRECT = "incorrect"      # Misconception or wrong answer
    CONFUSED = "confused"        # Student doesn't know / asks for help
    OFF_TOPIC = "off_topic"      # Unrelated to the concept
    ACKNOWLEDGMENT = "ack"       # Short response: "ok", "sure", "yes"
    DEEP_INSIGHT = "deep"        # Student shows deeper-than-expected understanding


# Transition table: (current_state, response_category) → next_state
TRANSITIONS: dict[tuple[SocraticState, ResponseCategory], SocraticState] = {
    # OPENING — after greeting, always probe
    (SocraticState.OPENING, ResponseCategory.CORRECT): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.PARTIALLY_CORRECT): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.INCORRECT): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.CONFUSED): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.OFF_TOPIC): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.ACKNOWLEDGMENT): SocraticState.PROBE,
    (SocraticState.OPENING, ResponseCategory.DEEP_INSIGHT): SocraticState.PROBE,

    # PROBE — branch based on understanding
    (SocraticState.PROBE, ResponseCategory.CORRECT): SocraticState.CONFIRM,
    (SocraticState.PROBE, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.PROBE, ResponseCategory.INCORRECT): SocraticState.REDIRECT,
    (SocraticState.PROBE, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.PROBE, ResponseCategory.OFF_TOPIC): SocraticState.REDIRECT,
    (SocraticState.PROBE, ResponseCategory.ACKNOWLEDGMENT): SocraticState.PROBE,
    (SocraticState.PROBE, ResponseCategory.DEEP_INSIGHT): SocraticState.DEEPEN,

    # SCAFFOLD — keep scaffolding or advance
    (SocraticState.SCAFFOLD, ResponseCategory.CORRECT): SocraticState.CONFIRM,
    (SocraticState.SCAFFOLD, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.SCAFFOLD, ResponseCategory.INCORRECT): SocraticState.REDIRECT,
    (SocraticState.SCAFFOLD, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.SCAFFOLD, ResponseCategory.OFF_TOPIC): SocraticState.REDIRECT,
    (SocraticState.SCAFFOLD, ResponseCategory.ACKNOWLEDGMENT): SocraticState.SCAFFOLD,
    (SocraticState.SCAFFOLD, ResponseCategory.DEEP_INSIGHT): SocraticState.DEEPEN,

    # REDIRECT — try to get back on track
    (SocraticState.REDIRECT, ResponseCategory.CORRECT): SocraticState.CONFIRM,
    (SocraticState.REDIRECT, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.REDIRECT, ResponseCategory.INCORRECT): SocraticState.SCAFFOLD,
    (SocraticState.REDIRECT, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.REDIRECT, ResponseCategory.OFF_TOPIC): SocraticState.PROBE,
    (SocraticState.REDIRECT, ResponseCategory.ACKNOWLEDGMENT): SocraticState.SCAFFOLD,
    (SocraticState.REDIRECT, ResponseCategory.DEEP_INSIGHT): SocraticState.DEEPEN,

    # CONFIRM — verified understanding, go deeper or close
    (SocraticState.CONFIRM, ResponseCategory.CORRECT): SocraticState.DEEPEN,
    (SocraticState.CONFIRM, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.CONFIRM, ResponseCategory.INCORRECT): SocraticState.REDIRECT,
    (SocraticState.CONFIRM, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.CONFIRM, ResponseCategory.OFF_TOPIC): SocraticState.PROBE,
    (SocraticState.CONFIRM, ResponseCategory.ACKNOWLEDGMENT): SocraticState.DEEPEN,
    (SocraticState.CONFIRM, ResponseCategory.DEEP_INSIGHT): SocraticState.DEEPEN,

    # DEEPEN — push further or wrap up
    (SocraticState.DEEPEN, ResponseCategory.CORRECT): SocraticState.CLOSE,
    (SocraticState.DEEPEN, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.DEEPEN, ResponseCategory.INCORRECT): SocraticState.REDIRECT,
    (SocraticState.DEEPEN, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.DEEPEN, ResponseCategory.OFF_TOPIC): SocraticState.PROBE,
    (SocraticState.DEEPEN, ResponseCategory.ACKNOWLEDGMENT): SocraticState.DEEPEN,
    (SocraticState.DEEPEN, ResponseCategory.DEEP_INSIGHT): SocraticState.CLOSE,

    # CLOSE — session ending, but can re-open if needed
    (SocraticState.CLOSE, ResponseCategory.CORRECT): SocraticState.CLOSE,
    (SocraticState.CLOSE, ResponseCategory.PARTIALLY_CORRECT): SocraticState.SCAFFOLD,
    (SocraticState.CLOSE, ResponseCategory.INCORRECT): SocraticState.REDIRECT,
    (SocraticState.CLOSE, ResponseCategory.CONFUSED): SocraticState.SCAFFOLD,
    (SocraticState.CLOSE, ResponseCategory.OFF_TOPIC): SocraticState.CLOSE,
    (SocraticState.CLOSE, ResponseCategory.ACKNOWLEDGMENT): SocraticState.CLOSE,
    (SocraticState.CLOSE, ResponseCategory.DEEP_INSIGHT): SocraticState.CLOSE,
}


class SocraticStateMachine:
    """Manages Socratic state transitions for a tutoring session."""

    def __init__(self):
        self.state = SocraticState.OPENING
        self.turn_count = 0
        self.state_history: list[SocraticState] = [SocraticState.OPENING]

    def transition(self, category: ResponseCategory) -> SocraticState:
        """Advance the state machine based on the student's response category.

        Returns the new state after transition.
        """
        self.turn_count += 1
        key = (self.state, category)
        new_state = TRANSITIONS.get(key, SocraticState.SCAFFOLD)
        self.state = new_state
        self.state_history.append(new_state)
        return new_state

    def reset(self):
        """Reset to initial state."""
        self.state = SocraticState.OPENING
        self.turn_count = 0
        self.state_history = [SocraticState.OPENING]
