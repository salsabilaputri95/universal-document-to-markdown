"""Tests for Markdown parsing and export to DOCX, PDF, and PPTX."""

import docx
import pptx
import pypdfium2
from PIL import Image

from core.markdown_exporter import MarkdownExporter
from core.md_parser import (
    CodeBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
    parse_markdown,
    runs_to_plain_text,
)

SAMPLE_MARKDOWN = """---
title: Test Document
author: OmniMark
---

# Main Project Title

Introductory paragraph with **bold text**, *italic text*, ~~strikethrough~~, `inline code`, and [link](https://example.com).

## Implementation Steps

1. Setup environment
2. Install dependencies
   1. Install python-docx
   2. Install reportlab
3. Run verification

## Key Features

- Local processing
- Multi-format output
  - Word document
  - PDF document
  - PowerPoint presentation

## Data Overview

| Name | Role | Status |
|:-----|:----:|-------:|
| Alice | Lead | Active |
| Bob | Dev | Pending |

### Technical Notes

> Important: Do not send data to external cloud.

```python
def check_status():
    return True
```

---

![Sample Image](images/diagram.png)
"""


def test_parse_markdown_comprehensive():
    doc = parse_markdown(SAMPLE_MARKDOWN)

    assert doc.title == "Main Project Title"
    assert doc.frontmatter.get("title") == "Test Document"

    # Verify block types
    types = [type(b) for b in doc.blocks]
    assert HeadingBlock in types
    assert ParagraphBlock in types
    assert ListBlock in types
    assert TableBlock in types
    assert QuoteBlock in types
    assert CodeBlock in types

    # Check headings
    headings = [b for b in doc.blocks if isinstance(b, HeadingBlock)]
    assert headings[0].level == 1
    assert runs_to_plain_text(headings[0].runs) == "Main Project Title"
    assert headings[1].level == 2
    assert runs_to_plain_text(headings[1].runs) == "Implementation Steps"

    # Check table
    tables = [b for b in doc.blocks if isinstance(b, TableBlock)]
    assert len(tables) == 1
    tbl = tables[0]
    assert len(tbl.header) == 3
    assert runs_to_plain_text(tbl.header[0]) == "Name"
    assert len(tbl.rows) == 2
    assert tbl.aligns == ["left", "center", "right"]

    # Check lists
    lists = [b for b in doc.blocks if isinstance(b, ListBlock)]
    assert len(lists) == 2
    assert lists[0].ordered is True
    assert len(lists[0].items) == 3
    assert lists[1].ordered is False
    assert len(lists[1].items) == 2


def test_render_docx_output(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    img_file = img_dir / "diagram.png"
    Image.new("RGB", (200, 100), color="blue").save(img_file)

    exporter = MarkdownExporter()
    res = exporter.export_text(
        markdown_text=SAMPLE_MARKDOWN,
        base_name="sample.md",
        formats=["docx"],
        output_dir=tmp_path / "out",
        base_dirs=[tmp_path],
    )

    assert res.success_count == 1
    docx_file = res.files[0].output_path
    assert docx_file is not None and docx_file.is_file()

    # Inspect docx content
    doc = docx.Document(docx_file)
    p_texts = [p.text for p in doc.paragraphs]
    assert any("Main Project Title" in t for t in p_texts)
    assert any("Setup environment" in t for t in p_texts)
    assert any("Local processing" in t for t in p_texts)

    # Check tables
    assert len(doc.tables) == 1
    assert doc.tables[0].cell(0, 0).text == "Name"
    assert doc.tables[0].cell(1, 0).text == "Alice"

    # Check image was included
    assert len(doc.inline_shapes) == 1


def test_render_pdf_output(tmp_path):
    exporter = MarkdownExporter(page_size="A4")
    res = exporter.export_text(
        markdown_text=SAMPLE_MARKDOWN,
        base_name="sample.md",
        formats=["pdf"],
        output_dir=tmp_path / "out",
        base_dirs=[tmp_path],
    )

    assert res.success_count == 1
    pdf_file = res.files[0].output_path
    assert pdf_file is not None and pdf_file.is_file()

    # Inspect PDF using pypdfium2
    pdf_doc = pypdfium2.PdfDocument(pdf_file)
    assert len(pdf_doc) >= 1
    extracted_text = "".join(page.get_textpage().get_text_range() for page in pdf_doc)
    assert "Main Project Title" in extracted_text
    assert "Implementation Steps" in extracted_text
    assert "Alice" in extracted_text
    pdf_doc.close()


def test_render_pptx_output(tmp_path):
    exporter = MarkdownExporter(slide_split_level=2)
    res = exporter.export_text(
        markdown_text=SAMPLE_MARKDOWN,
        base_name="sample.md",
        formats=["pptx"],
        output_dir=tmp_path / "out",
        base_dirs=[tmp_path],
    )

    assert res.success_count == 1
    pptx_file = res.files[0].output_path
    assert pptx_file is not None and pptx_file.is_file()

    prs = pptx.Presentation(pptx_file)
    assert len(prs.slides) >= 3

    slide_titles = [s.shapes.title.text for s in prs.slides if s.shapes.title]
    assert any("Main Project Title" in t for t in slide_titles)
    assert any("Implementation Steps" in t for t in slide_titles)
    assert any("Key Features" in t for t in slide_titles)


def test_export_all_formats_together(tmp_path):
    md_file = tmp_path / "test_doc.md"
    md_file.write_text("# Quick Test\n\n- Bullet 1\n- Bullet 2\n", encoding="utf-8")

    exporter = MarkdownExporter()
    res = exporter.export_file(
        path=md_file,
        formats=["docx", "pdf", "pptx"],
        output_dir=tmp_path / "all_out",
    )

    assert res.success_count == 3
    for f in res.files:
        assert f.success is True
        assert f.output_path is not None
        assert f.output_path.is_file()
        assert f.file_size_bytes > 0


def test_export_file_validations(tmp_path):
    exporter = MarkdownExporter()

    # 1. Non-existent file
    res = exporter.export_file(tmp_path / "missing.md", ["docx"])
    assert "tidak ditemukan" in (res.error_message or "")

    # 2. Wrong extension
    bad_ext = tmp_path / "bad.txt"
    bad_ext.write_text("content")
    res = exporter.export_file(bad_ext, ["docx"])
    assert "tidak didukung" in (res.error_message or "")

    # 3. Empty file
    empty_file = tmp_path / "empty.md"
    empty_file.touch()
    res = exporter.export_file(empty_file, ["docx"])
    assert "kosong" in (res.error_message or "")

    # 4. Binary file
    bin_file = tmp_path / "binary.md"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04")
    res = exporter.export_file(bin_file, ["docx"])
    assert "biner" in (res.error_message or "")
