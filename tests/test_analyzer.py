"""Tests for writing_tools.analyzer."""

from __future__ import annotations

import pytest

from writing_tools.analyzer import TextAnalyzer, TextStats, _count_syllables

# ---------------------------------------------------------------------------
# _count_syllables
# ---------------------------------------------------------------------------


class TestCountSyllables:
    def test_single_vowel_word(self):
        assert _count_syllables("cat") == 1

    def test_two_syllable_word(self):
        assert _count_syllables("river") == 2

    def test_silent_e_not_counted(self):
        # "cake" → ca-ke, but silent 'e' rule reduces count to 1
        assert _count_syllables("cake") == 1

    def test_multi_syllable(self):
        assert _count_syllables("beautiful") >= 3

    def test_empty_string_returns_zero(self):
        assert _count_syllables("") == 0

    def test_punctuation_stripped(self):
        assert _count_syllables("cat.") == _count_syllables("cat")


# ---------------------------------------------------------------------------
# TextAnalyzer — construction
# ---------------------------------------------------------------------------


class TestTextAnalyzerConstruction:
    def test_accepts_valid_text(self):
        analyzer = TextAnalyzer("Hello world.")
        assert analyzer.text == "Hello world."

    def test_raises_on_non_string_text(self):
        with pytest.raises(TypeError):
            TextAnalyzer(123)  # type: ignore[arg-type]

    def test_raises_on_negative_top_n(self):
        with pytest.raises(ValueError):
            TextAnalyzer("text", top_n=-1)

    def test_accepts_zero_top_n(self):
        analyzer = TextAnalyzer("hello world", top_n=0)
        assert analyzer.top_words() == []


# ---------------------------------------------------------------------------
# word_count
# ---------------------------------------------------------------------------


SIMPLE_TEXT = "The quick brown fox jumps over the lazy dog."


class TestWordCount:
    def test_simple_sentence(self):
        assert TextAnalyzer(SIMPLE_TEXT).word_count() == 9

    def test_empty_text_returns_zero(self):
        assert TextAnalyzer("").word_count() == 0

    def test_numbers_not_counted_as_words(self):
        assert TextAnalyzer("3 cats and 2 dogs").word_count() == 3

    def test_hyphenated_words(self):
        # "well-known" is two tokens separated by a hyphen
        assert TextAnalyzer("well-known fact").word_count() == 3


# ---------------------------------------------------------------------------
# sentence_count
# ---------------------------------------------------------------------------


class TestSentenceCount:
    def test_single_sentence(self):
        assert TextAnalyzer("Hello world.").sentence_count() == 1

    def test_multiple_sentences(self):
        text = "Hello world. How are you? I am fine!"
        assert TextAnalyzer(text).sentence_count() == 3

    def test_empty_text_returns_zero(self):
        assert TextAnalyzer("").sentence_count() == 0


# ---------------------------------------------------------------------------
# paragraph_count
# ---------------------------------------------------------------------------


MULTI_PARA = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."


class TestParagraphCount:
    def test_multi_paragraph(self):
        assert TextAnalyzer(MULTI_PARA).paragraph_count() == 3

    def test_single_paragraph(self):
        assert TextAnalyzer("No blank lines here.").paragraph_count() == 1

    def test_empty_text_returns_zero(self):
        assert TextAnalyzer("").paragraph_count() == 0


# ---------------------------------------------------------------------------
# character_count
# ---------------------------------------------------------------------------


class TestCharacterCount:
    def test_with_spaces(self):
        assert TextAnalyzer("abc def").character_count(include_spaces=True) == 7

    def test_without_spaces(self):
        assert TextAnalyzer("abc def").character_count(include_spaces=False) == 6

    def test_empty_text(self):
        assert TextAnalyzer("").character_count() == 0


# ---------------------------------------------------------------------------
# flesch_reading_ease
# ---------------------------------------------------------------------------


class TestFleschReadingEase:
    def test_empty_text_returns_zero(self):
        assert TextAnalyzer("").flesch_reading_ease() == 0.0

    def test_score_within_valid_range(self):
        score = TextAnalyzer(SIMPLE_TEXT).flesch_reading_ease()
        assert 0.0 <= score <= 100.0

    def test_simple_text_scores_higher_than_complex(self):
        simple = "The cat sat on the mat."
        complex_ = (
            "The multifaceted epistemological implications of contemporary "
            "poststructuralist theoretical frameworks necessitate comprehensive "
            "interdisciplinary investigation methodologies."
        )
        assert (
            TextAnalyzer(simple).flesch_reading_ease()
            > TextAnalyzer(complex_).flesch_reading_ease()
        )


# ---------------------------------------------------------------------------
# top_words
# ---------------------------------------------------------------------------


class TestTopWords:
    def test_returns_most_frequent(self):
        text = "book book book chapter chapter"
        top = TextAnalyzer(text, top_n=2).top_words()
        words = [w for w, _ in top]
        assert "book" in words
        assert "chapter" in words

    def test_excludes_stop_words(self):
        text = "the the the cat sat on the mat"
        top = TextAnalyzer(text).top_words()
        words = [w for w, _ in top]
        assert "the" not in words

    def test_respects_n_parameter(self):
        text = " ".join(f"word{i}" * (10 - i) for i in range(10))
        top = TextAnalyzer(text).top_words(n=3)
        assert len(top) <= 3

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            TextAnalyzer("hello").top_words(n=-1)

    def test_zero_n_returns_empty(self):
        assert TextAnalyzer("hello world").top_words(n=0) == []


# ---------------------------------------------------------------------------
# analyse — integration
# ---------------------------------------------------------------------------


class TestAnalyse:
    def test_returns_text_stats(self):
        stats = TextAnalyzer(SIMPLE_TEXT).analyse()
        assert isinstance(stats, TextStats)

    def test_stats_word_count_matches(self):
        analyzer = TextAnalyzer(SIMPLE_TEXT)
        assert analyzer.analyse().word_count == analyzer.word_count()

    def test_reading_level_label(self):
        stats = TextAnalyzer(SIMPLE_TEXT).analyse()
        assert isinstance(stats.reading_level, str)
        assert stats.reading_level != ""


# ---------------------------------------------------------------------------
# TextStats.reading_level boundaries
# ---------------------------------------------------------------------------


class TestReadingLevel:
    def _stats_with_score(self, score: float) -> TextStats:
        return TextStats(
            word_count=10, sentence_count=1, paragraph_count=1,
            character_count=50, character_count_no_spaces=40,
            avg_words_per_sentence=10.0, avg_sentences_per_paragraph=1.0,
            flesch_reading_ease=score,
        )

    @pytest.mark.parametrize("score,expected", [
        (95, "Very Easy"),
        (85, "Easy"),
        (75, "Fairly Easy"),
        (65, "Standard"),
        (55, "Fairly Difficult"),
        (40, "Difficult"),
        (20, "Very Confusing"),
    ])
    def test_labels(self, score, expected):
        assert self._stats_with_score(score).reading_level == expected
