"""Unit tests for sentence boundary chunker."""

import pytest
from pipeline.sentence_chunker import SentenceChunker


class TestSentenceChunker:
    def setup_method(self):
        self.chunker = SentenceChunker(min_chars=10, max_chars=500)

    def test_init_defaults(self):
        c = SentenceChunker()
        assert c.min_chars == 10
        assert c.max_chars == 500
        assert c._buffer == ""

    def test_single_sentence_with_period(self):
        """Complete sentence ending with period should be emitted."""
        tokens = ["Hello", " world", " this", " is", " a", " test", "."]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 1
        assert results[0] == "Hello world this is a test."

    def test_single_sentence_with_question_mark(self):
        """Complete sentence ending with ? should be emitted."""
        tokens = ["What", " do", " you", " think", " about", " that", "?"]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 1
        assert "?" in results[0]

    def test_single_sentence_with_exclamation(self):
        """Complete sentence ending with ! should be emitted."""
        tokens = ["That", " is", " really", " great", "!"]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 1
        assert "!" in results[0]

    def test_two_sentences(self):
        """Two sentences should produce two emissions."""
        tokens = ["First", " sentence", ". ", "Second", " sentence", " here", "."]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 2
        assert "First" in results[0]
        assert "Second" in results[1]

    def test_min_chars_threshold(self):
        """Short text shouldn't trigger emission even with punctuation."""
        # "Hi." is only 3 chars, below min_chars=10
        result = self.chunker.add_token("Hi.")
        assert result is None

    def test_flush_returns_remaining(self):
        """Flush should return accumulated text."""
        self.chunker.add_token("Hello")
        self.chunker.add_token(" world")
        result = self.chunker.flush()
        assert result == "Hello world"

    def test_flush_empty_returns_none(self):
        """Flush on empty buffer should return None."""
        result = self.chunker.flush()
        assert result is None

    def test_reset_clears_buffer(self):
        """Reset should clear the buffer."""
        self.chunker.add_token("Hello")
        self.chunker.reset()
        assert self.chunker._buffer == ""

    def test_max_chars_forces_emission(self):
        """Buffer exceeding max_chars should force emission."""
        chunker = SentenceChunker(min_chars=5, max_chars=20)
        # Add enough text to exceed max_chars
        result = None
        for i in range(10):
            r = chunker.add_token("word ")
            if r is not None:
                result = r
                break
        assert result is not None

    def test_abbreviation_not_treated_as_boundary(self):
        """Abbreviations like 'Dr.' should not trigger sentence boundary."""
        tokens = ["Hello", " Dr.", " Smith"]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        # "Hello Dr." shouldn't emit since "dr." is an abbreviation
        assert len(results) == 0

    def test_multiple_punctuation(self):
        """Multiple punctuation marks (e.g., '...') should trigger boundary."""
        tokens = ["That", " is", " interesting", "...", " "]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 1

    def test_question_in_quotes(self):
        """Question mark inside quotes should trigger boundary."""
        tokens = ["She", " asked", ' "why', "?\"", " "]
        results = []
        for t in tokens:
            r = self.chunker.add_token(t)
            if r is not None:
                results.append(r)
        assert len(results) == 1

    def test_streaming_tokens_character_by_character(self):
        """Should work with single-character tokens (common in LLM streaming)."""
        text = "Hello world. "
        results = []
        for char in text:
            r = self.chunker.add_token(char)
            if r is not None:
                results.append(r)
        assert len(results) == 1
        assert results[0] == "Hello world."

    def test_flush_after_stream_end(self):
        """After stream ends, flush should return any remaining text."""
        for char in "Partial sentence":
            self.chunker.add_token(char)
        result = self.chunker.flush()
        assert result == "Partial sentence"

    def test_empty_tokens_ignored(self):
        """Empty string tokens shouldn't cause issues."""
        self.chunker.add_token("")
        self.chunker.add_token("")
        assert self.chunker._buffer == ""
