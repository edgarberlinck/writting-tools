"""Text analysis utilities for book writing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class TextStats:
    """Aggregated statistics for a piece of text."""

    word_count: int
    sentence_count: int
    paragraph_count: int
    character_count: int
    character_count_no_spaces: int
    avg_words_per_sentence: float
    avg_sentences_per_paragraph: float
    flesch_reading_ease: float
    top_words: list[tuple[str, int]] = field(default_factory=list)

    @property
    def reading_level(self) -> str:
        """Human-readable label derived from the Flesch Reading Ease score."""
        score = self.flesch_reading_ease
        if score >= 90:
            return "Very Easy"
        if score >= 80:
            return "Easy"
        if score >= 70:
            return "Fairly Easy"
        if score >= 60:
            return "Standard"
        if score >= 50:
            return "Fairly Difficult"
        if score >= 30:
            return "Difficult"
        return "Very Confusing"


# Words that carry little meaning and should be ignored in frequency lists.
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "but", "or", "for", "nor", "on", "at",
        "to", "by", "in", "of", "up", "as", "is", "it", "be", "do",
        "if", "he", "she", "we", "i", "you", "my", "his", "her", "its",
        "our", "their", "this", "that", "was", "are", "not", "with",
        "had", "has", "have", "from", "they", "them", "what", "who",
        "which", "when", "where", "how", "so", "than", "then", "there",
        "were", "been", "will", "would", "could", "should", "may", "can",
        "did", "does", "into", "about", "after", "before", "through",
        "over", "under", "again", "no", "more", "also", "just", "all",
        "any", "each", "few", "most", "other", "some", "such", "only",
        "own", "same", "too", "very", "s", "t", "don", "now",
    }
)


def _count_syllables(word: str) -> int:
    """Estimate the number of syllables in an English word.

    Uses a vowel-cluster heuristic that is good enough for readability
    scoring purposes.
    """
    word = word.lower().strip(".,!?;:\"'")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    # Silent trailing 'e'
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


class TextAnalyzer:
    """Analyse a piece of text and compute writing statistics.

    Parameters
    ----------
    text:
        The raw text to analyse.
    top_n:
        Number of most-frequent non-stop words to include in the report.
    """

    def __init__(self, text: str, top_n: int = 10) -> None:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, got {type(text).__name__}")
        if top_n < 0:
            raise ValueError("top_n must be a non-negative integer")
        self._text = text
        self._top_n = top_n

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def text(self) -> str:
        return self._text

    def word_count(self) -> int:
        """Return the total number of words."""
        return len(self._words())

    def sentence_count(self) -> int:
        """Return the total number of sentences."""
        return len(self._sentences())

    def paragraph_count(self) -> int:
        """Return the total number of non-empty paragraphs."""
        return len(self._paragraphs())

    def character_count(self, include_spaces: bool = True) -> int:
        """Return the number of characters.

        Parameters
        ----------
        include_spaces:
            When *False*, whitespace is excluded from the count.
        """
        if include_spaces:
            return len(self._text)
        return sum(1 for c in self._text if not c.isspace())

    def flesch_reading_ease(self) -> float:
        """Compute the Flesch Reading Ease score.

        The formula is:
            206.835 - 1.015 * (words / sentences)
                    - 84.6  * (syllables / words)

        Returns 0.0 for empty texts.
        """
        words = self._words()
        sentences = self._sentences()
        if not words or not sentences:
            return 0.0
        total_syllables = sum(_count_syllables(w) for w in words)
        score = (
            206.835
            - 1.015 * (len(words) / len(sentences))
            - 84.6 * (total_syllables / len(words))
        )
        return round(max(0.0, min(100.0, score)), 2)

    def top_words(self, n: int | None = None) -> list[tuple[str, int]]:
        """Return the *n* most frequent non-stop words as (word, count) pairs.

        Parameters
        ----------
        n:
            Number of words to return.  Defaults to the *top_n* value
            supplied at construction time.
        """
        if n is None:
            n = self._top_n
        if n < 0:
            raise ValueError("n must be a non-negative integer")
        freq: dict[str, int] = {}
        for word in self._words():
            normalised = word.lower()
            if normalised not in _STOP_WORDS:
                freq[normalised] = freq.get(normalised, 0) + 1
        return sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def analyse(self) -> TextStats:
        """Return a :class:`TextStats` snapshot of the current text."""
        words = self._words()
        sentences = self._sentences()
        paragraphs = self._paragraphs()
        word_cnt = len(words)
        sentence_cnt = len(sentences)
        paragraph_cnt = len(paragraphs)

        avg_wps = word_cnt / sentence_cnt if sentence_cnt else 0.0
        avg_spp = sentence_cnt / paragraph_cnt if paragraph_cnt else 0.0

        return TextStats(
            word_count=word_cnt,
            sentence_count=sentence_cnt,
            paragraph_count=paragraph_cnt,
            character_count=self.character_count(include_spaces=True),
            character_count_no_spaces=self.character_count(include_spaces=False),
            avg_words_per_sentence=round(avg_wps, 2),
            avg_sentences_per_paragraph=round(avg_spp, 2),
            flesch_reading_ease=self.flesch_reading_ease(),
            top_words=self.top_words(),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _words(self) -> list[str]:
        return re.findall(r"\b[A-Za-z']+\b", self._text)

    def _sentences(self) -> list[str]:
        raw = re.split(r"(?<=[.!?])\s+", self._text.strip())
        return [s for s in raw if s.strip()]

    def _paragraphs(self) -> list[str]:
        raw = re.split(r"\n{2,}", self._text.strip())
        return [p for p in raw if p.strip()]
