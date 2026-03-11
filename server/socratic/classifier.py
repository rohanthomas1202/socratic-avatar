"""Rule-based query classifier for student responses.

Classifies student utterances into ResponseCategory values to drive
state machine transitions. Uses heuristics first, with an optional
LLM fallback for ambiguous cases.
"""

import logging
import re

from socratic.state_machine import ResponseCategory

logger = logging.getLogger(__name__)

# Short acknowledgment patterns
ACK_PATTERNS = [
    r"^(ok|okay|sure|yes|yeah|yep|yup|got it|i see|alright|right|uh huh|mhm|hmm|ah)\.?$",
    r"^(i understand|i get it|makes sense|that makes sense|oh|oh ok|oh okay|cool|interesting)\.?$",
]

# Confusion / help-seeking patterns
CONFUSED_PATTERNS = [
    r"i don'?t (know|understand|get it)",
    r"i'?m (confused|lost|not sure|unsure)",
    r"(what|huh|can you (explain|help|tell me))",
    r"i have no (idea|clue)",
    r"(help|explain)",
    r"^(no idea|not sure|idk|dunno)\.?$",
]

# Indicators of deeper thinking
DEEP_INDICATORS = [
    r"(because|since|therefore|so that means|which means|implies|connects to)",
    r"(real.world|in practice|application|similar to|like when|analogy)",
    r"(what if|i wonder|could it also|does this mean|would that apply)",
]

# Correctness indicators (checked against concept keywords at runtime)
CORRECT_HEDGES = [
    r"(i think|maybe|probably|could be|might be|i guess)",
]


def classify_response(
    student_text: str,
    concept_keywords: list[str] | None = None,
    expected_ideas: list[str] | None = None,
) -> ResponseCategory:
    """Classify a student's response using rule-based heuristics.

    Args:
        student_text: The student's transcribed response.
        concept_keywords: Key terms related to the concept (for relevance check).
        expected_ideas: Key ideas the student should demonstrate.

    Returns:
        A ResponseCategory indicating how to interpret the student's response.
    """
    text = student_text.strip().lower()

    if not text:
        return ResponseCategory.ACKNOWLEDGMENT

    # 1. Check for short acknowledgments
    for pattern in ACK_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return ResponseCategory.ACKNOWLEDGMENT

    # 2. Check for confusion / help-seeking
    # But if the student mentions expected ideas, they're not truly confused
    has_confusion_signal = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in CONFUSED_PATTERNS
    )
    if has_confusion_signal and not expected_ideas:
        return ResponseCategory.CONFUSED
    if has_confusion_signal and expected_ideas:
        # Check if they also mention correct ideas — if so, that's partial, not confused
        idea_matches = sum(1 for idea in expected_ideas if idea.lower() in text)
        if idea_matches == 0:
            return ResponseCategory.CONFUSED
        # Fall through to correctness check below

    # 3. Check for deep insight indicators
    deep_count = 0
    for pattern in DEEP_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            deep_count += 1
    # Deep insight = at least one causal indicator + sufficient length
    if deep_count >= 1 and len(text.split()) >= 15:
        return ResponseCategory.DEEP_INSIGHT

    # 4. Check off-topic (if concept keywords provided)
    if concept_keywords:
        on_topic = any(kw.lower() in text for kw in concept_keywords)
        if not on_topic and len(text.split()) > 5:
            return ResponseCategory.OFF_TOPIC

    # 5. Assess correctness based on expected ideas
    if expected_ideas:
        matches = sum(1 for idea in expected_ideas if idea.lower() in text)
        if matches >= 2:
            return ResponseCategory.CORRECT
        elif matches == 1:
            return ResponseCategory.PARTIALLY_CORRECT

    # 6. Length-based heuristics for remaining cases
    word_count = len(text.split())
    if word_count <= 3:
        return ResponseCategory.ACKNOWLEDGMENT
    elif word_count <= 8:
        # Short answer with some content — likely partial
        return ResponseCategory.PARTIALLY_CORRECT
    else:
        # Longer response — default to partial (let the LLM probe further)
        return ResponseCategory.PARTIALLY_CORRECT


def get_concept_keywords(concept_id: str) -> list[str]:
    """Get relevance-check keywords for a concept."""
    keyword_map = {
        "division_by_zero": [
            "divide", "division", "zero", "undefined", "infinity",
            "multiply", "multiplication", "quotient", "divisor",
        ],
        "photosynthesis": [
            "plant", "sun", "light", "chlorophyll", "oxygen", "carbon",
            "glucose", "sugar", "leaf", "leaves", "energy", "water",
        ],
        "gravity": [
            "gravity", "fall", "weight", "mass", "pull", "attract",
            "orbit", "planet", "earth", "force", "newton",
        ],
        "fractions": [
            "fraction", "half", "numerator", "denominator", "divide",
            "part", "whole", "equal", "piece", "slice", "pizza",
        ],
        "water_cycle": [
            "evaporate", "evaporation", "condense", "condensation",
            "rain", "cloud", "water", "vapor", "precipitation", "cycle",
        ],
    }
    return keyword_map.get(concept_id, [])


def get_expected_ideas(concept_id: str) -> list[str]:
    """Get simplified expected-idea keywords for correctness checking."""
    idea_map = {
        "division_by_zero": [
            "undefined", "no answer", "can't divide",
            "multiply by zero", "inverse", "grows larger",
        ],
        "photosynthesis": [
            "sunlight", "carbon dioxide", "glucose", "chlorophyll",
            "oxygen", "energy", "sugar",
        ],
        "gravity": [
            "mass", "attract", "pull", "center",
            "orbit", "inverse square",
        ],
        "fractions": [
            "part of a whole", "equal parts", "denominator",
            "numerator", "equivalent",
        ],
        "water_cycle": [
            "evaporation", "condensation", "precipitation",
            "water vapor", "cycle",
        ],
    }
    return idea_map.get(concept_id, [])
