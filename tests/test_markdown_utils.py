"""Unit tests for markdown utilities."""

from utils.markdown_utils import count_markdown_stats, format_markdown_output


def test_count_markdown_stats():
    text = "# Title\nThis is a sample document with five words.\n"
    stats = count_markdown_stats(text)
    assert stats["characters"] == len(text)
    assert stats["words"] >= 8
    assert stats["lines"] == 2


def test_count_markdown_stats_empty():
    stats = count_markdown_stats("")
    assert stats["characters"] == 0
    assert stats["words"] == 0
    assert stats["lines"] == 0


def test_format_markdown_standard():
    raw = "## Heading\nParagraph content."
    formatted = format_markdown_output(raw, style="standard")
    assert formatted == raw


def test_format_markdown_with_metadata():
    raw = "## Heading\nContent"
    metadata = {
        "filename": "test.pdf",
        "extension": ".pdf",
        "file_size_formatted": "12 KB",
        "engine": "Docling",
    }
    formatted = format_markdown_output(raw, style="with_metadata", metadata=metadata)
    assert "source_file: test.pdf" in formatted
    assert "engine_used: Docling" in formatted
    assert "## Heading" in formatted


def test_format_markdown_rag():
    raw = "## Section 1\nImportant info"
    metadata = {"filename": "kb.pdf", "engine": "Docling"}
    formatted = format_markdown_output(raw, style="rag", metadata=metadata)
    assert "<!-- BEGIN DOCUMENT METADATA -->" in formatted
    assert "<!-- SECTION CONTENT START -->" in formatted
    assert "Important info" in formatted

