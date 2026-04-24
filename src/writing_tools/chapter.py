"""Chapter and Document management for book writing."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chapter:
    """A single chapter in a book.

    Parameters
    ----------
    title:
        The chapter title.
    content:
        The body text of the chapter.
    number:
        Optional explicit chapter number.  If *None*, it is inferred from
        the chapter's position inside a :class:`Document`.
    """

    title: str
    content: str = ""
    number: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Chapter title must be a non-empty string")
        if not isinstance(self.content, str):
            raise TypeError("Chapter content must be a string")
        if self.number is not None and self.number < 1:
            raise ValueError("Chapter number must be a positive integer")

    @property
    def word_count(self) -> int:
        """Return the word count of this chapter's content."""
        return len(re.findall(r"\b[A-Za-z']+\b", self.content))

    def append(self, text: str) -> None:
        """Append *text* to the chapter content.

        A blank line is inserted between existing content and the new text
        if the content is not already empty.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if self.content:
            self.content = f"{self.content}\n\n{text}"
        else:
            self.content = text

    def to_markdown(self, chapter_number: int | None = None) -> str:
        """Render the chapter as a Markdown string.

        Parameters
        ----------
        chapter_number:
            Overrides ``self.number`` when rendering the heading.  If
            neither is set, the heading will not include a number.
        """
        num = chapter_number if chapter_number is not None else self.number
        heading = f"## Chapter {num}: {self.title}" if num else f"## {self.title}"
        return f"{heading}\n\n{self.content}"

    def to_plain_text(self, chapter_number: int | None = None) -> str:
        """Render the chapter as plain text."""
        num = chapter_number if chapter_number is not None else self.number
        heading = f"Chapter {num}: {self.title}" if num else self.title
        separator = "=" * len(heading)
        return f"{heading}\n{separator}\n\n{self.content}"


class Document:
    """A full book / document composed of ordered :class:`Chapter` objects.

    Parameters
    ----------
    title:
        The document (book) title.
    author:
        The author name.
    """

    def __init__(self, title: str, author: str = "") -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Document title must be a non-empty string")
        self.title = title
        self.author = author
        self._chapters: list[Chapter] = []

    # ------------------------------------------------------------------
    # Chapter management
    # ------------------------------------------------------------------

    def add_chapter(self, chapter: Chapter) -> None:
        """Append *chapter* to the end of the document."""
        if not isinstance(chapter, Chapter):
            raise TypeError("chapter must be a Chapter instance")
        self._chapters.append(chapter)

    def remove_chapter(self, index: int) -> Chapter:
        """Remove and return the chapter at *index* (0-based).

        Raises
        ------
        IndexError
            If *index* is out of range.
        """
        if not 0 <= index < len(self._chapters):
            raise IndexError(
                f"Chapter index {index} is out of range "
                f"(document has {len(self._chapters)} chapters)"
            )
        return self._chapters.pop(index)

    def move_chapter(self, from_index: int, to_index: int) -> None:
        """Move a chapter from *from_index* to *to_index*.

        Both indices are 0-based positions in the current chapter list.

        Raises
        ------
        IndexError
            If either index is out of range.
        """
        n = len(self._chapters)
        for idx, name in ((from_index, "from_index"), (to_index, "to_index")):
            if not 0 <= idx < n:
                raise IndexError(
                    f"{name} {idx} is out of range (document has {n} chapters)"
                )
        chapter = self._chapters.pop(from_index)
        self._chapters.insert(to_index, chapter)

    def get_chapter(self, index: int) -> Chapter:
        """Return the chapter at *index* (0-based) without removing it."""
        if not 0 <= index < len(self._chapters):
            raise IndexError(
                f"Chapter index {index} is out of range "
                f"(document has {len(self._chapters)} chapters)"
            )
        return self._chapters[index]

    def find_chapters(self, query: str) -> list[tuple[int, Chapter]]:
        """Return a list of ``(index, chapter)`` pairs whose titles or content
        contain *query* (case-insensitive).
        """
        query_lower = query.lower()
        return [
            (i, ch)
            for i, ch in enumerate(self._chapters)
            if query_lower in ch.title.lower() or query_lower in ch.content.lower()
        ]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def chapters(self) -> list[Chapter]:
        """A shallow copy of the internal chapter list."""
        return list(self._chapters)

    @property
    def chapter_count(self) -> int:
        """Total number of chapters."""
        return len(self._chapters)

    @property
    def total_word_count(self) -> int:
        """Sum of word counts across all chapters."""
        return sum(ch.word_count for ch in self._chapters)

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[Chapter]:
        return iter(self._chapters)

    def __len__(self) -> int:
        return len(self._chapters)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_markdown(self) -> str:
        """Render the entire document as a Markdown string."""
        parts: list[str] = [f"# {self.title}"]
        if self.author:
            parts.append(f"*by {self.author}*")
        parts.append("")
        for i, chapter in enumerate(self._chapters, start=1):
            parts.append(chapter.to_markdown(chapter_number=i))
            parts.append("")
        return "\n".join(parts)

    def to_plain_text(self) -> str:
        """Render the entire document as plain text."""
        title_line = f"{self.title}"
        sep = "=" * len(title_line)
        parts: list[str] = [title_line, sep]
        if self.author:
            parts.append(f"by {self.author}")
        parts.append("")
        for i, chapter in enumerate(self._chapters, start=1):
            parts.append(chapter.to_plain_text(chapter_number=i))
            parts.append("")
        return "\n".join(parts)

    def save(self, path: str | Path, fmt: str = "markdown") -> Path:
        """Save the document to *path*.

        Parameters
        ----------
        path:
            Destination file path.
        fmt:
            ``"markdown"`` (default) or ``"text"``.

        Returns
        -------
        Path
            The resolved path of the saved file.

        Raises
        ------
        ValueError
            If *fmt* is not ``"markdown"`` or ``"text"``.
        """
        path = Path(path)
        if fmt == "markdown":
            content = self.to_markdown()
        elif fmt == "text":
            content = self.to_plain_text()
        else:
            raise ValueError(f"Unknown format '{fmt}'. Use 'markdown' or 'text'.")
        path.write_text(content, encoding="utf-8")
        return path.resolve()

    @classmethod
    def load_markdown(cls, path: str | Path) -> Document:
        """Parse a Markdown file previously saved by :meth:`save` and return
        a :class:`Document`.

        This is a best-effort parser that understands the format produced by
        :meth:`to_markdown`.  External Markdown documents may not parse
        correctly.
        """
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        title = ""
        author = ""
        chapters: list[Chapter] = []
        current_title: str | None = None
        current_content_lines: list[str] = []

        for line in lines:
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("*by ") and line.endswith("*"):
                author = line[4:-1].strip()
            elif re.match(r"^## Chapter \d+: .+", line):
                if current_title is not None:
                    chapters.append(
                        Chapter(
                            title=current_title,
                            content="\n".join(current_content_lines).strip(),
                        )
                    )
                    current_content_lines = []
                current_title = re.sub(r"^## Chapter \d+: ", "", line).strip()
            elif line.startswith("## ") and not re.match(r"^## Chapter \d+:", line):
                if current_title is not None:
                    chapters.append(
                        Chapter(
                            title=current_title,
                            content="\n".join(current_content_lines).strip(),
                        )
                    )
                    current_content_lines = []
                current_title = line[3:].strip()
            elif current_title is not None:
                current_content_lines.append(line)

        if current_title is not None:
            chapters.append(
                Chapter(
                    title=current_title,
                    content="\n".join(current_content_lines).strip(),
                )
            )

        doc = cls(title=title or "Untitled", author=author)
        for ch in chapters:
            doc.add_chapter(ch)
        return doc
