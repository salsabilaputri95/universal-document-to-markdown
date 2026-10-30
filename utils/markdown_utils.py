"""Markdown processing and formatting utilities."""

import re
from datetime import datetime
from typing import Any


def count_markdown_stats(text: str) -> dict[str, int]:
    """Calculate character and word counts from markdown text."""
    if not text:
        return {"characters": 0, "characters_no_spaces": 0, "words": 0, "lines": 0}

    lines = text.splitlines()
    characters = len(text)
    characters_no_spaces = len(re.sub(r"\s+", "", text))
    words = len(re.findall(r"\b\w+\b", text))

    return {
        "characters": characters,
        "characters_no_spaces": characters_no_spaces,
        "words": words,
        "lines": len(lines),
    }


def format_markdown_output(
    markdown_text: str,
    style: str = "standard",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Format markdown text according to the requested style:

    - 'standard': Clean markdown as extracted
    - 'with_metadata': Prepends a clean YAML/Markdown metadata block
    - 'with_images': Retains image references with clear captions/links
    - 'rag': Optimized for chunking and retrieval (explicit section delimiters & source headers)
    """
    clean_text = markdown_text.strip()
    meta = metadata or {}

    if style == "with_metadata":
        header_lines = [
            "---",
            f"source_file: {meta.get('filename', 'unknown')}",
            f"file_type: {meta.get('extension', 'unknown')}",
            f"file_size: {meta.get('file_size_formatted', 'unknown')}",
            f"engine_used: {meta.get('engine', 'unknown')}",
            f"converted_at: {meta.get('converted_at', datetime.now().isoformat())}",
        ]
        if "pages" in meta:
            header_lines.append(f"pages_or_sheets: {meta['pages']}")
        header_lines.append("---\n")
        return "\n".join(header_lines) + "\n" + clean_text

    elif style == "rag":
        rag_lines = [
            "<!-- BEGIN DOCUMENT METADATA -->",
            f"# Document: {meta.get('filename', 'Document')}",
            f"- **Source**: {meta.get('filename', 'Unknown')}",
            f"- **Engine**: {meta.get('engine', 'Unknown')}",
            f"- **Timestamp**: {meta.get('converted_at', datetime.now().isoformat())}",
            "<!-- END DOCUMENT METADATA -->\n",
            "<!-- SECTION CONTENT START -->",
            clean_text,
            "<!-- SECTION CONTENT END -->",
        ]
        return "\n".join(rag_lines)

    # Default 'standard' or 'with_images'
    return clean_text

