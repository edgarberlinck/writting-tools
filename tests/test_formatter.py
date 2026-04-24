"""Tests for writing_tools.formatter."""

from __future__ import annotations

import pytest

from writing_tools.formatter import TextFormatter

# ---------------------------------------------------------------------------
# normalize_whitespace
# ---------------------------------------------------------------------------


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        result = TextFormatter.normalize_whitespace("hello   world")
        assert result == "hello world"

    def test_strips_leading_trailing_per_line(self):
        result = TextFormatter.normalize_whitespace("  hello  \n  world  ")
        assert result == "hello\nworld"

    def test_preserves_newlines(self):
        result = TextFormatter.normalize_whitespace("line1\nline2")
        assert "\n" in result

    def test_empty_string(self):
        assert TextFormatter.normalize_whitespace("") == ""


# ---------------------------------------------------------------------------
# normalize_line_endings
# ---------------------------------------------------------------------------


class TestNormalizeLineEndings:
    def test_crlf_to_lf(self):
        assert TextFormatter.normalize_line_endings("a\r\nb") == "a\nb"

    def test_cr_to_lf(self):
        assert TextFormatter.normalize_line_endings("a\rb") == "a\nb"

    def test_lf_unchanged(self):
        assert TextFormatter.normalize_line_endings("a\nb") == "a\nb"

    def test_mixed(self):
        result = TextFormatter.normalize_line_endings("a\r\nb\rc\nd")
        assert "\r" not in result


# ---------------------------------------------------------------------------
# remove_extra_blank_lines
# ---------------------------------------------------------------------------


class TestRemoveExtraBlankLines:
    def test_reduces_triple_blank_to_double(self):
        text = "a\n\n\n\nb"
        result = TextFormatter.remove_extra_blank_lines(text, max_consecutive=2)
        assert "\n\n\n\n" not in result

    def test_double_blank_preserved_when_max_2(self):
        text = "a\n\nb"
        result = TextFormatter.remove_extra_blank_lines(text, max_consecutive=2)
        assert result == text

    def test_negative_max_raises(self):
        with pytest.raises(ValueError):
            TextFormatter.remove_extra_blank_lines("text", max_consecutive=-1)

    def test_zero_max_collapses_all_blanks(self):
        text = "a\n\nb"
        result = TextFormatter.remove_extra_blank_lines(text, max_consecutive=0)
        assert "\n\n" not in result


# ---------------------------------------------------------------------------
# wrap_text
# ---------------------------------------------------------------------------


class TestWrapText:
    def test_no_line_exceeds_width(self):
        text = "word " * 30
        wrapped = TextFormatter.wrap_text(text, width=40)
        for line in wrapped.splitlines():
            assert len(line) <= 40

    def test_preserves_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph."
        result = TextFormatter.wrap_text(text, width=79)
        assert "\n\n" in result

    def test_invalid_width_raises(self):
        with pytest.raises(ValueError):
            TextFormatter.wrap_text("hello", width=0)


# ---------------------------------------------------------------------------
# sentence_case
# ---------------------------------------------------------------------------


class TestSentenceCase:
    def test_capitalises_start_of_sentence(self):
        result = TextFormatter.sentence_case("hello world. this is a test.")
        assert result.startswith("Hello")

    def test_capitalises_after_period(self):
        result = TextFormatter.sentence_case("first. second sentence.")
        assert "Second" in result

    def test_already_correct(self):
        text = "Hello world. This is fine."
        assert TextFormatter.sentence_case(text) == text


# ---------------------------------------------------------------------------
# title_case
# ---------------------------------------------------------------------------


class TestTitleCase:
    def test_capitalises_major_words(self):
        result = TextFormatter.title_case("the old man and the sea")
        assert result.startswith("The")
        assert "Man" in result
        assert "Sea" in result

    def test_articles_stay_lower_in_middle(self):
        result = TextFormatter.title_case("the old man and the sea")
        # "and" and inner "the" should stay lower
        assert " and " in result
        parts = result.split()
        assert parts[3] == "and"

    def test_first_word_always_capitalised(self):
        result = TextFormatter.title_case("a tale of two cities")
        assert result[0].isupper()


# ---------------------------------------------------------------------------
# fix_punctuation_spacing
# ---------------------------------------------------------------------------


class TestFixPunctuationSpacing:
    def test_removes_space_before_comma(self):
        result = TextFormatter.fix_punctuation_spacing("hello , world")
        assert " ," not in result

    def test_adds_space_after_period(self):
        result = TextFormatter.fix_punctuation_spacing("Hello.World")
        assert "Hello. World" in result

    def test_no_double_space_inserted(self):
        result = TextFormatter.fix_punctuation_spacing("Hello. World")
        assert "Hello.  World" not in result


# ---------------------------------------------------------------------------
# convert_quotes
# ---------------------------------------------------------------------------


class TestConvertQuotes:
    def test_straight_to_typographic_double(self):
        result = TextFormatter.convert_quotes('"hello"')
        assert "\u201c" in result or "\u201d" in result

    def test_typographic_to_straight(self):
        text = "\u201chello\u201d"
        result = TextFormatter.convert_quotes(text, style="straight")
        assert '"' in result
        assert "\u201c" not in result

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            TextFormatter.convert_quotes("text", style="unknown")


# ---------------------------------------------------------------------------
# find_and_replace
# ---------------------------------------------------------------------------


class TestFindAndReplace:
    def test_single_replacement(self):
        result = TextFormatter.find_and_replace("Hello world", [("world", "Python")])
        assert result == "Hello Python"

    def test_multiple_replacements_applied_in_order(self):
        result = TextFormatter.find_and_replace(
            "aaa",
            [("aaa", "bbb"), ("bbb", "ccc")],
        )
        assert result == "ccc"

    def test_case_insensitive(self):
        result = TextFormatter.find_and_replace(
            "Hello WORLD",
            [("world", "Python")],
            case_sensitive=False,
        )
        assert "Python" in result

    def test_case_sensitive_no_match(self):
        result = TextFormatter.find_and_replace(
            "Hello WORLD",
            [("world", "Python")],
            case_sensitive=True,
        )
        assert "Python" not in result

    def test_empty_replacements(self):
        assert TextFormatter.find_and_replace("unchanged", []) == "unchanged"


# ---------------------------------------------------------------------------
# pipe
# ---------------------------------------------------------------------------


class TestPipe:
    def test_applies_operations_in_order(self):
        result = TextFormatter.pipe(
            "  hello   world  ",
            TextFormatter.normalize_whitespace,
        )
        assert result == "hello world"

    def test_no_operations_returns_original(self):
        assert TextFormatter.pipe("hello") == "hello"

    def test_multiple_operations(self):
        result = TextFormatter.pipe(
            "hello\r\nworld",
            TextFormatter.normalize_line_endings,
            TextFormatter.normalize_whitespace,
        )
        assert "\r" not in result
        assert result == "hello\nworld"
