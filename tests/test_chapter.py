"""Tests for writing_tools.chapter."""

from __future__ import annotations

import pytest

from writing_tools.chapter import Chapter, Document

# ---------------------------------------------------------------------------
# Chapter — construction
# ---------------------------------------------------------------------------


class TestChapterConstruction:
    def test_valid_chapter(self):
        ch = Chapter(title="Beginning", content="Once upon a time.")
        assert ch.title == "Beginning"
        assert ch.content == "Once upon a time."

    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            Chapter(title="")

    def test_whitespace_only_title_raises(self):
        with pytest.raises(ValueError):
            Chapter(title="   ")

    def test_non_string_content_raises(self):
        with pytest.raises(TypeError):
            Chapter(title="Ch1", content=42)  # type: ignore[arg-type]

    def test_negative_number_raises(self):
        with pytest.raises(ValueError):
            Chapter(title="Ch1", number=0)

    def test_positive_number_accepted(self):
        ch = Chapter(title="Ch1", number=3)
        assert ch.number == 3


# ---------------------------------------------------------------------------
# Chapter.word_count
# ---------------------------------------------------------------------------


class TestChapterWordCount:
    def test_simple_content(self):
        ch = Chapter(title="Test", content="Hello world my friend")
        assert ch.word_count == 4

    def test_empty_content(self):
        ch = Chapter(title="Test")
        assert ch.word_count == 0


# ---------------------------------------------------------------------------
# Chapter.append
# ---------------------------------------------------------------------------


class TestChapterAppend:
    def test_append_to_empty(self):
        ch = Chapter(title="Ch", content="")
        ch.append("New text.")
        assert ch.content == "New text."

    def test_append_to_existing(self):
        ch = Chapter(title="Ch", content="First.")
        ch.append("Second.")
        assert "First." in ch.content
        assert "Second." in ch.content
        assert "\n\n" in ch.content

    def test_non_string_raises(self):
        ch = Chapter(title="Ch")
        with pytest.raises(TypeError):
            ch.append(123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Chapter.to_markdown
# ---------------------------------------------------------------------------


class TestChapterToMarkdown:
    def test_with_number(self):
        ch = Chapter(title="The Start", content="Body text.")
        md = ch.to_markdown(chapter_number=1)
        assert md.startswith("## Chapter 1: The Start")
        assert "Body text." in md

    def test_without_number(self):
        ch = Chapter(title="Untitled Chapter", content="Content.")
        md = ch.to_markdown()
        assert md.startswith("## Untitled Chapter")

    def test_instance_number_used_when_no_override(self):
        ch = Chapter(title="Ch", content=".", number=5)
        assert "Chapter 5" in ch.to_markdown()


# ---------------------------------------------------------------------------
# Chapter.to_plain_text
# ---------------------------------------------------------------------------


class TestChapterToPlainText:
    def test_separator_length(self):
        ch = Chapter(title="Short", content="Body.", number=2)
        lines = ch.to_plain_text().splitlines()
        heading_line = lines[0]
        separator_line = lines[1]
        assert len(separator_line) == len(heading_line)

    def test_content_present(self):
        ch = Chapter(title="Test", content="Hello world.", number=1)
        assert "Hello world." in ch.to_plain_text()


# ---------------------------------------------------------------------------
# Document — construction
# ---------------------------------------------------------------------------


class TestDocumentConstruction:
    def test_valid_document(self):
        doc = Document(title="My Book", author="Author")
        assert doc.title == "My Book"
        assert doc.author == "Author"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            Document(title="")

    def test_default_author_is_empty(self):
        doc = Document(title="Book")
        assert doc.author == ""


# ---------------------------------------------------------------------------
# Document — chapter management
# ---------------------------------------------------------------------------


class TestDocumentChapterManagement:
    def _make_doc(self) -> Document:
        doc = Document(title="Book")
        doc.add_chapter(Chapter(title="Intro", content="Intro text."))
        doc.add_chapter(Chapter(title="Middle", content="Middle text."))
        doc.add_chapter(Chapter(title="End", content="End text."))
        return doc

    def test_add_chapter_increases_count(self):
        doc = Document(title="Book")
        doc.add_chapter(Chapter(title="Ch1"))
        assert doc.chapter_count == 1

    def test_add_non_chapter_raises(self):
        doc = Document(title="Book")
        with pytest.raises(TypeError):
            doc.add_chapter("not a chapter")  # type: ignore[arg-type]

    def test_remove_chapter_returns_chapter(self):
        doc = self._make_doc()
        ch = doc.remove_chapter(0)
        assert ch.title == "Intro"
        assert doc.chapter_count == 2

    def test_remove_out_of_range_raises(self):
        doc = Document(title="Book")
        with pytest.raises(IndexError):
            doc.remove_chapter(0)

    def test_move_chapter(self):
        doc = self._make_doc()
        doc.move_chapter(0, 2)  # Move "Intro" to last position
        assert doc.get_chapter(2).title == "Intro"

    def test_move_chapter_out_of_range_raises(self):
        doc = self._make_doc()
        with pytest.raises(IndexError):
            doc.move_chapter(0, 10)

    def test_get_chapter(self):
        doc = self._make_doc()
        assert doc.get_chapter(1).title == "Middle"

    def test_get_chapter_out_of_range_raises(self):
        doc = Document(title="Book")
        with pytest.raises(IndexError):
            doc.get_chapter(0)

    def test_find_chapters_by_title(self):
        doc = self._make_doc()
        results = doc.find_chapters("intro")
        assert len(results) == 1
        assert results[0][1].title == "Intro"

    def test_find_chapters_by_content(self):
        doc = self._make_doc()
        results = doc.find_chapters("Middle text")
        assert len(results) == 1

    def test_find_chapters_no_match(self):
        doc = self._make_doc()
        assert doc.find_chapters("xyzzy") == []

    def test_iter_chapters(self):
        doc = self._make_doc()
        titles = [ch.title for ch in doc]
        assert titles == ["Intro", "Middle", "End"]

    def test_len(self):
        doc = self._make_doc()
        assert len(doc) == 3

    def test_chapters_property_is_copy(self):
        doc = self._make_doc()
        chapters = doc.chapters
        chapters.clear()
        assert doc.chapter_count == 3  # Internal list unchanged


# ---------------------------------------------------------------------------
# Document — word count
# ---------------------------------------------------------------------------


class TestDocumentWordCount:
    def test_total_word_count(self):
        doc = Document(title="Book")
        doc.add_chapter(Chapter(title="Ch1", content="one two three"))
        doc.add_chapter(Chapter(title="Ch2", content="four five"))
        assert doc.total_word_count == 5

    def test_empty_document(self):
        doc = Document(title="Book")
        assert doc.total_word_count == 0


# ---------------------------------------------------------------------------
# Document — serialisation
# ---------------------------------------------------------------------------


class TestDocumentMarkdown:
    def test_title_in_markdown(self):
        doc = Document(title="My Book", author="Jane")
        assert "# My Book" in doc.to_markdown()

    def test_author_in_markdown(self):
        doc = Document(title="Book", author="Jane")
        assert "Jane" in doc.to_markdown()

    def test_chapter_in_markdown(self):
        doc = Document(title="Book")
        doc.add_chapter(Chapter(title="Ch1", content="Content here."))
        md = doc.to_markdown()
        assert "## Chapter 1: Ch1" in md
        assert "Content here." in md


class TestDocumentPlainText:
    def test_title_present(self):
        doc = Document(title="My Book")
        assert "My Book" in doc.to_plain_text()

    def test_chapter_present(self):
        doc = Document(title="Book")
        doc.add_chapter(Chapter(title="Intro", content="Hello."))
        assert "Intro" in doc.to_plain_text()


# ---------------------------------------------------------------------------
# Document.save / load_markdown — round-trip
# ---------------------------------------------------------------------------


class TestDocumentSaveLoad:
    def test_save_and_load_markdown(self, tmp_path):
        doc = Document(title="Round Trip", author="Tester")
        doc.add_chapter(Chapter(title="First", content="Body one."))
        doc.add_chapter(Chapter(title="Second", content="Body two."))

        saved_path = doc.save(tmp_path / "book.md", fmt="markdown")
        loaded = Document.load_markdown(saved_path)

        assert loaded.title == "Round Trip"
        assert loaded.author == "Tester"
        assert loaded.chapter_count == 2
        assert loaded.get_chapter(0).title == "First"
        assert loaded.get_chapter(1).title == "Second"

    def test_save_plain_text(self, tmp_path):
        doc = Document(title="Plain Book")
        doc.add_chapter(Chapter(title="Ch1", content="Content."))
        path = doc.save(tmp_path / "book.txt", fmt="text")
        text = path.read_text(encoding="utf-8")
        assert "Plain Book" in text
        assert "Content." in text

    def test_save_invalid_format_raises(self, tmp_path):
        doc = Document(title="Book")
        with pytest.raises(ValueError):
            doc.save(tmp_path / "book.xyz", fmt="invalid")
