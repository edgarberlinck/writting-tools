"""Text formatting utilities for book writing."""

from __future__ import annotations

import re
import textwrap
from collections.abc import Sequence


class TextFormatter:
    """A collection of text-transformation helpers.

    All methods are *pure* (they return new strings and never mutate
    the input) and can be chained via the fluent interface by using
    :meth:`pipe`.
    """

    # ------------------------------------------------------------------
    # White-space & structure
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapse consecutive spaces/tabs into a single space and strip
        leading/trailing whitespace from each line.
        """
        lines = text.splitlines()
        normalised = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        return "\n".join(normalised)

    @staticmethod
    def normalize_line_endings(text: str) -> str:
        """Convert all CR+LF and bare CR to LF."""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def remove_extra_blank_lines(text: str, max_consecutive: int = 2) -> str:
        """Reduce runs of blank lines to at most *max_consecutive* blank lines.

        Parameters
        ----------
        text:
            Input text.
        max_consecutive:
            Maximum number of consecutive blank lines to allow.
        """
        if max_consecutive < 0:
            raise ValueError("max_consecutive must be a non-negative integer")
        pattern = r"\n{" + str(max_consecutive + 2) + r",}"
        replacement = "\n" * (max_consecutive + 1)
        return re.sub(pattern, replacement, text)

    @staticmethod
    def wrap_text(text: str, width: int = 79) -> str:
        """Hard-wrap *text* to *width* characters, preserving paragraph
        breaks (double newlines).
        """
        if width < 1:
            raise ValueError("width must be a positive integer")
        paragraphs = re.split(r"\n{2,}", text)
        wrapped = [textwrap.fill(p, width=width) for p in paragraphs]
        return "\n\n".join(wrapped)

    # ------------------------------------------------------------------
    # Capitalisation
    # ------------------------------------------------------------------

    @staticmethod
    def sentence_case(text: str) -> str:
        """Capitalise the first letter of every sentence."""

        def _capitalise_match(m: re.Match) -> str:  # type: ignore[type-arg]
            return m.group(0).upper()

        return re.sub(r"(?:^|(?<=[.!?])\s+)([a-z])", _capitalise_match, text)

    @staticmethod
    def title_case(text: str) -> str:
        """Apply title-case capitalisation, honouring common English articles,
        conjunctions, and short prepositions.
        """
        _LOWER_WORDS: frozenset[str] = frozenset(
            {
                "a", "an", "the", "and", "but", "or", "for", "nor",
                "on", "at", "to", "by", "in", "of", "up", "as",
                "vs", "via", "with",
            }
        )
        words = text.split()
        result: list[str] = []
        for i, word in enumerate(words):
            clean = word.strip(".,!?;:\"'")
            if i == 0 or clean.lower() not in _LOWER_WORDS:
                result.append(word[0].upper() + word[1:] if word else word)
            else:
                result.append(word.lower())
        return " ".join(result)

    # ------------------------------------------------------------------
    # Punctuation
    # ------------------------------------------------------------------

    @staticmethod
    def fix_punctuation_spacing(text: str) -> str:
        """Ensure there is no space *before* punctuation and exactly one
        space *after* sentence-ending punctuation.
        """
        # Remove space before punctuation
        text = re.sub(r" +([.,!?;:])", r"\1", text)
        # Ensure single space after sentence-ending punctuation (. ! ?)
        text = re.sub(r"([.!?])(?=[A-Za-z])", r"\1 ", text)
        return text

    @staticmethod
    def convert_quotes(text: str, style: str = "typographic") -> str:
        """Convert straight quotes to the requested style.

        Parameters
        ----------
        text:
            Input text.
        style:
            ``"typographic"`` (default) — convert to curly quotes.
            ``"straight"``    — convert to straight quotes.
        """
        if style == "typographic":
            # Opening double quotes (after space, newline, or start)
            text = re.sub(r'(^|[\s(])"', lambda m: m.group(1) + "\u201c", text)
            # Closing double quotes
            text = text.replace('"', "\u201d")
            # Opening single quotes
            text = re.sub(r"(^|[\s(])'", lambda m: m.group(1) + "\u2018", text)
            # Closing single quotes / apostrophes
            text = text.replace("'", "\u2019")
        elif style == "straight":
            text = text.replace("\u201c", '"').replace("\u201d", '"')
            text = text.replace("\u2018", "'").replace("\u2019", "'")
        else:
            raise ValueError(
                f"Unknown quote style '{style}'. Use 'typographic' or 'straight'."
            )
        return text

    # ------------------------------------------------------------------
    # Search & replace
    # ------------------------------------------------------------------

    @staticmethod
    def find_and_replace(
        text: str,
        replacements: Sequence[tuple[str, str]],
        *,
        case_sensitive: bool = True,
    ) -> str:
        """Apply a sequence of (pattern, replacement) substitutions.

        Parameters
        ----------
        text:
            Input text.
        replacements:
            Ordered sequence of ``(old, new)`` literal-string pairs.
        case_sensitive:
            When *False*, matching ignores case.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        for old, new in replacements:
            text = re.sub(re.escape(old), new, text, flags=flags)
        return text

    # ------------------------------------------------------------------
    # Fluent helper
    # ------------------------------------------------------------------

    @staticmethod
    def pipe(text: str, *operations) -> str:  # type: ignore[no-untyped-def]
        """Apply a sequence of callables to *text* in order.

        Each callable must accept a single ``str`` argument and return a
        ``str``.  This enables easy composition without nesting:

        .. code-block:: python

            result = TextFormatter.pipe(
                raw_text,
                TextFormatter.normalize_line_endings,
                TextFormatter.normalize_whitespace,
                TextFormatter.fix_punctuation_spacing,
            )
        """
        result = text
        for op in operations:
            result = op(result)
        return result
