"""Tests for writing_tools.cli."""

from __future__ import annotations

import pytest

from writing_tools.cli import build_parser, main


class TestBuildParser:
    def test_analyse_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["analyse", "some_file.txt"])
        assert args.command == "analyse"
        assert args.file == "some_file.txt"
        assert args.top_n == 10

    def test_format_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["format", "file.txt"])
        assert args.command == "format"
        assert args.output is None

    def test_convert_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["convert", "book.md"])
        assert args.command == "convert"

    def test_no_subcommand_exits(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args([])


class TestCliAnalyse:
    def test_analyse_file(self, tmp_path):
        txt = tmp_path / "sample.txt"
        txt.write_text(
            "The quick brown fox. It jumps over the lazy dog.",
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc_info:
            main(["analyse", str(txt)])
        assert exc_info.value.code == 0

    def test_analyse_missing_file_exits_nonzero(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["analyse", str(tmp_path / "nonexistent.txt")])
        assert exc_info.value.code == 1


class TestCliFormat:
    def test_format_file_in_place(self, tmp_path):
        txt = tmp_path / "messy.txt"
        txt.write_text("Hello   world.\r\n\r\nNew  paragraph.", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            main(["format", str(txt)])
        assert exc_info.value.code == 0
        content = txt.read_text(encoding="utf-8")
        assert "  " not in content or "\r\n" not in content

    def test_format_with_output_file(self, tmp_path):
        src = tmp_path / "src.txt"
        out = tmp_path / "out.txt"
        src.write_text("Hello   world.", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            main(["format", str(src), "-o", str(out)])
        assert exc_info.value.code == 0
        assert out.exists()

    def test_format_missing_file_exits_nonzero(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["format", str(tmp_path / "missing.txt")])
        assert exc_info.value.code == 1


class TestCliConvert:
    def test_convert_md_to_txt(self, tmp_path):
        md = tmp_path / "book.md"
        md.write_text(
            "# My Book\n\n## Chapter 1: Start\n\nContent here.",
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc_info:
            main(["convert", str(md)])
        assert exc_info.value.code == 0
        out = tmp_path / "book.txt"
        assert out.exists()

    def test_convert_non_md_exits_nonzero(self, tmp_path):
        txt = tmp_path / "plain.txt"
        txt.write_text("Some text.", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            main(["convert", str(txt)])
        assert exc_info.value.code == 1

    def test_convert_missing_file_exits_nonzero(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["convert", str(tmp_path / "missing.md")])
        assert exc_info.value.code == 1
