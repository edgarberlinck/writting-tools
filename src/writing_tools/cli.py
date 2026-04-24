"""Command-line interface for writing-tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from writing_tools.analyzer import TextAnalyzer
from writing_tools.chapter import Document
from writing_tools.formatter import TextFormatter


def _cmd_analyse(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    analyzer = TextAnalyzer(text, top_n=args.top_n)
    stats = analyzer.analyse()

    print(f"File          : {path}")
    print(f"Words         : {stats.word_count}")
    print(f"Sentences     : {stats.sentence_count}")
    print(f"Paragraphs    : {stats.paragraph_count}")
    print(f"Characters    : {stats.character_count}")
    print(f"Avg words/sentence : {stats.avg_words_per_sentence}")
    print(f"Flesch score  : {stats.flesch_reading_ease} ({stats.reading_level})")
    if stats.top_words:
        print("\nTop words:")
        for word, count in stats.top_words:
            print(f"  {word:<20} {count}")
    return 0


def _cmd_format(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    text = TextFormatter.pipe(
        text,
        TextFormatter.normalize_line_endings,
        TextFormatter.normalize_whitespace,
        TextFormatter.fix_punctuation_spacing,
        lambda t: TextFormatter.remove_extra_blank_lines(t, max_consecutive=2),
    )

    out_path = Path(args.output) if args.output else path
    out_path.write_text(text, encoding="utf-8")
    print(f"Formatted text written to {out_path}")
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1
    if path.suffix.lower() not in (".md", ".markdown"):
        print(
            "Error: only Markdown (.md) input files are supported for conversion.",
            file=sys.stderr,
        )
        return 1

    doc = Document.load_markdown(path)
    out_path = Path(args.output) if args.output else path.with_suffix(".txt")
    doc.save(out_path, fmt="text")
    print(f"Converted '{path}' → '{out_path}'")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="writing-tools",
        description="Simple and effective tools to write books.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # analyse
    p_analyse = sub.add_parser("analyse", help="Analyse text statistics of a file.")
    p_analyse.add_argument("file", help="Path to the text file.")
    p_analyse.add_argument(
        "--top-n", type=int, default=10, dest="top_n",
        help="Number of top frequent words to display (default: 10).",
    )
    p_analyse.set_defaults(func=_cmd_analyse)

    # format
    p_format = sub.add_parser("format", help="Clean up and normalise a text file.")
    p_format.add_argument("file", help="Path to the text file.")
    p_format.add_argument(
        "-o", "--output", default=None,
        help="Output file path (default: overwrite input).",
    )
    p_format.set_defaults(func=_cmd_format)

    # convert
    p_convert = sub.add_parser(
        "convert", help="Convert a Markdown document to plain text."
    )
    p_convert.add_argument("file", help="Path to the Markdown file.")
    p_convert.add_argument("-o", "--output", default=None, help="Output file path.")
    p_convert.set_defaults(func=_cmd_convert)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
