"""Sentence boundary chunker for streaming LLM → TTS pipeline.

Accumulates streaming LLM tokens and emits complete sentences,
enabling the TTS to produce natural-sounding speech with proper
prosody. Adds ~50ms latency for the first sentence but significantly
improves TTS output quality.
"""

import re


class SentenceChunker:
    """Accumulates tokens and emits complete sentences."""

    # Sentence-ending punctuation followed by space or end of string
    SENTENCE_END_PATTERN = re.compile(r'[.!?]+[\s"\')\]]*$')
    # Abbreviations that shouldn't trigger sentence breaks
    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.",
        "vs.", "etc.", "inc.", "ltd.", "dept.", "est.",
        "approx.", "avg.", "e.g.", "i.e.", "fig.", "vol.",
    }

    def __init__(self, min_chars: int = 10, max_chars: int = 500):
        """
        Args:
            min_chars: Minimum characters before checking for sentence boundary.
            max_chars: Maximum characters to accumulate before forcing emission.
        """
        self.min_chars = min_chars
        self.max_chars = max_chars
        self._buffer = ""

    def add_token(self, token: str) -> str | None:
        """Add a token and return a complete sentence if boundary detected.

        Args:
            token: A streaming token from the LLM.

        Returns:
            A complete sentence string, or None if still accumulating.
        """
        self._buffer += token

        # Don't check for boundaries until we have enough text
        if len(self._buffer) < self.min_chars:
            return None

        # Force emit if buffer is too long
        if len(self._buffer) >= self.max_chars:
            return self._flush()

        # Check for sentence boundary
        if self._is_sentence_boundary():
            return self._flush()

        return None

    def flush(self) -> str | None:
        """Flush any remaining text in the buffer.

        Call this when the LLM stream ends to get the final partial sentence.

        Returns:
            Remaining text, or None if buffer is empty.
        """
        return self._flush()

    def reset(self):
        """Clear the buffer."""
        self._buffer = ""

    def _flush(self) -> str | None:
        """Emit the current buffer contents and reset."""
        text = self._buffer.strip()
        self._buffer = ""
        return text if text else None

    def _is_sentence_boundary(self) -> bool:
        """Check if the buffer ends at a sentence boundary."""
        text = self._buffer.strip()
        if not text:
            return False

        # Check for sentence-ending punctuation
        if not self.SENTENCE_END_PATTERN.search(text):
            return False

        # Check it's not an abbreviation (must be a standalone word)
        lower = text.lower()
        for abbr in self.ABBREVIATIONS:
            if lower.endswith(abbr):
                # Check the abbreviation is a whole word (preceded by space or start)
                pos = len(lower) - len(abbr)
                if pos == 0 or lower[pos - 1] == " ":
                    return False

        return True
