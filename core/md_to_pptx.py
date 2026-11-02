"""Render a parsed MarkdownDocument into a PowerPoint (.pptx) presentation.

Slide mapping rules (explicit and predictable):
- A heading with level <= `split_level` starts a new slide and becomes its title.
- If the document starts with an H1 and `split_level` is 2, that H1 becomes a title slide.
- Deeper headings (H3+ or H2+ when split_level=1) become bold lines inside the slide body.
- Paragraphs, bullets, numbered lists, quotes, and code flow into the slide body text box.
- Tables and images get their own slide (large tables are split, header row repeated).
- A horizontal rule (`---`) forces a new slide (same convention as Marp/Deckset).
- When body text exceeds the slide capacity, it continues on a "(lanjutan)" slide.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from core.md_parser import (
    Block,
    CodeBlock,
    HeadingBlock,
    HorizontalRuleBlock,
    ImageBlock,
    InlineRun,
    ListBlock,
    MarkdownDocument,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
    runs_to_plain_text,
)
from core.md_render_common import ImageResolver, image_size_inches

SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
BODY_LEFT_IN = 0.6
BODY_TOP_IN = 1.45
BODY_W_IN = SLIDE_W_IN - 2 * BODY_LEFT_IN
BODY_H_IN = 5.6
MAX_TABLE_ROWS_PER_SLIDE = 10  # data rows (header repeated on each slide)
MONO_FONT = "Consolas"
_BULLET_CHARS = ["•", "–", "▪"]
_AUTONUM_TYPES = ["arabicPeriod", "alphaLcPeriod", "romanLcPeriod"]
_ALIGN_MAP = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
_LAYOUT_TITLE = 0
_LAYOUT_TITLE_ONLY = 5


@dataclass
class _Line:
    """One paragraph in a slide body."""

    runs: list[InlineRun]
    kind: str = "para"  # para | bullet | number | subheading | code | quote
    level: int = 0
    list_id: int = 0
    number: int = 1
    size: float = 20.0


@dataclass
class _SlideSpec:
    title: str
    lines: list[_Line] = field(default_factory=list)


class PptxRenderer:
    """Render MarkdownDocument blocks into a python-pptx Presentation."""

    def __init__(self, image_resolver: ImageResolver | None = None, split_level: int = 2):
        self.images = image_resolver or ImageResolver()
        self.split_level = 1 if split_level == 1 else 2
        self.warnings: list[str] = []
        self._list_counter = 0

    # ------------------------------------------------------------------ entry
    def render(self, doc_model: MarkdownDocument, output_path: Path, fallback_title: str = "") -> Path:
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W_IN)
        self.prs.slide_height = Inches(SLIDE_H_IN)
        self.current: _SlideSpec | None = None
        self.current_title = doc_model.title or fallback_title

        blocks = list(doc_model.blocks)
        if (
            self.split_level == 2
            and blocks
            and isinstance(blocks[0], HeadingBlock)
            and blocks[0].level == 1
        ):
            self._add_title_slide(runs_to_plain_text(blocks[0].runs))
            self.current_title = runs_to_plain_text(blocks[0].runs)
            blocks = blocks[1:]

        for block in blocks:
            self._handle_block(block)
        self._flush()

        if len(self.prs.slides) == 0:
            self._add_title_slide(self.current_title or "Presentasi")

        if doc_model.title:
            self.prs.core_properties.title = doc_model.title
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(output_path)
        self.warnings.extend(w for w in self.images.warnings if w not in self.warnings)
        return output_path

    # ------------------------------------------------------------------ block routing
    def _handle_block(self, block: Block) -> None:
        if isinstance(block, HeadingBlock):
            text = runs_to_plain_text(block.runs).strip()
            if block.level <= self.split_level:
                self._flush()
                self.current_title = text
                self.current = _SlideSpec(title=text)
            else:
                self._ensure_slide()
                self.current.lines.append(_Line(runs=block.runs, kind="subheading", size=22))
        elif isinstance(block, ParagraphBlock):
            self._ensure_slide()
            self.current.lines.append(_Line(runs=block.runs, kind="para"))
        elif isinstance(block, ListBlock):
            self._ensure_slide()
            self._collect_list(block, level=0)
        elif isinstance(block, QuoteBlock):
            self._ensure_slide()
            for inner in block.blocks:
                if isinstance(inner, ParagraphBlock):
                    self.current.lines.append(_Line(runs=inner.runs, kind="quote"))
                else:
                    self._handle_block(inner)
        elif isinstance(block, CodeBlock):
            self._ensure_slide()
            for code_line in block.code.split("\n"):
                self.current.lines.append(
                    _Line(runs=[InlineRun(text=code_line or " ", code=True)], kind="code", size=14)
                )
        elif isinstance(block, HorizontalRuleBlock):
            if self.current and self.current.lines:
                self._flush(keep_empty_heading_slide=False)
                self.current = _SlideSpec(title=self.current_title)
        elif isinstance(block, TableBlock):
            self._flush(keep_empty_heading_slide=False)
            self._add_table_slides(block)
        elif isinstance(block, ImageBlock):
            self._flush(keep_empty_heading_slide=False)
            self._add_image_slide(block)

    def _collect_list(self, block: ListBlock, level: int) -> None:
        self._list_counter += 1
        list_id = self._list_counter
        for idx, item in enumerate(block.items):
            self.current.lines.append(
                _Line(
                    runs=item.runs,
                    kind="number" if block.ordered else "bullet",
                    level=level,
                    list_id=list_id,
                    number=block.start + idx,
                    size=20 if level == 0 else 18,
                )
            )
            for child in item.children:
                if isinstance(child, ListBlock):
                    self._collect_list(child, level + 1)
                elif isinstance(child, ParagraphBlock):
                    self.current.lines.append(_Line(runs=child.runs, kind="para", level=level + 1, size=18))
                elif isinstance(child, CodeBlock):
                    for code_line in child.code.split("\n"):
                        self.current.lines.append(
                            _Line(runs=[InlineRun(text=code_line or " ", code=True)], kind="code", size=14)
                        )
                elif isinstance(child, (TableBlock, ImageBlock)):
                    self._flush()
                    self._handle_block(child)
                    self.current = _SlideSpec(title=self.current_title)

    def _ensure_slide(self) -> None:
        if self.current is None:
            self.current = _SlideSpec(title=self.current_title)

    # ------------------------------------------------------------------ text slides
    def _flush(self, keep_empty_heading_slide: bool = True) -> None:
        """Write the pending text slide(s), splitting when content exceeds capacity."""
        spec, self.current = self.current, None
        if spec is None:
            return
        if not spec.lines:
            # A heading with no body: produce a title slide only if requested
            if keep_empty_heading_slide:
                self._new_slide(spec.title)
            return
        capacity = BODY_H_IN * 72  # points
        chunk: list[_Line] = []
        used = 0.0
        part = 0
        for line in spec.lines:
            height = self._estimate_height(line)
            if chunk and used + height > capacity:
                self._write_text_slide(spec.title, chunk, continuation=part > 0)
                part += 1
                chunk, used = [], 0.0
            chunk.append(line)
            used += height
        if chunk:
            self._write_text_slide(spec.title, chunk, continuation=part > 0)

    @staticmethod
    def _estimate_height(line: _Line) -> float:
        indent_in = 0.375 * (line.level + (1 if line.kind in ("bullet", "number") else 0))
        width_pt = (BODY_W_IN - indent_in) * 72
        avg_char_pt = line.size * (0.6 if line.kind == "code" else 0.5)
        chars_per_line = max(10, int(width_pt / avg_char_pt))
        text = runs_to_plain_text(line.runs)
        n_lines = sum(max(1, math.ceil(len(seg) / chars_per_line)) for seg in text.split("\n"))
        spacing = 2 if line.kind == "code" else 6
        return n_lines * line.size * 1.2 + spacing

    def _new_slide(self, title: str):
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[_LAYOUT_TITLE_ONLY])
        title_shape = slide.shapes.title
        title_shape.text = title or " "
        title_shape.left, title_shape.top = Inches(BODY_LEFT_IN), Inches(0.35)
        title_shape.width, title_shape.height = Inches(BODY_W_IN), Inches(1.0)
        tf = title_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for paragraph in tf.paragraphs:
            paragraph.alignment = PP_ALIGN.LEFT
            for run in paragraph.runs:
                run.font.size = Pt(32)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        return slide

    def _write_text_slide(self, title: str, lines: list[_Line], continuation: bool) -> None:
        slide = self._new_slide(f"{title} (lanjutan)" if continuation and title else title)
        box = slide.shapes.add_textbox(
            Inches(BODY_LEFT_IN), Inches(BODY_TOP_IN), Inches(BODY_W_IN), Inches(BODY_H_IN)
        )
        tf = box.text_frame
        tf.word_wrap = True
        first_number_on_slide: dict[int, int] = {}

        for idx, line in enumerate(lines):
            paragraph = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            paragraph.space_after = Pt(2 if line.kind == "code" else 6)
            self._add_runs(paragraph, line)
            if line.kind == "bullet":
                self._set_bullet(paragraph, line.level)
            elif line.kind == "number":
                start = first_number_on_slide.setdefault(line.list_id, line.number)
                self._set_autonum(paragraph, line.level, start)
            else:
                self._set_no_bullet(paragraph, line.level)

    def _add_runs(self, paragraph, line: _Line) -> None:
        for model in line.runs:
            if model.line_break:
                paragraph.add_line_break()
                continue
            run = paragraph.add_run()
            run.text = model.text
            font = run.font
            font.size = Pt(line.size)
            font.bold = True if (model.bold or line.kind == "subheading") else None
            font.italic = True if (model.italic or line.kind == "quote") else None
            if model.code or line.kind == "code":
                font.name = MONO_FONT
                if line.kind != "code":
                    font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C)
            if line.kind == "quote":
                font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            if model.strike:
                run._r.get_or_add_rPr().set("strike", "sngStrike")
            if model.link:
                run.hyperlink.address = model.link
                font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
                font.underline = True

    # ------------------------------------------------------------------ bullet XML
    @staticmethod
    def _reset_pPr(paragraph, level: int, has_bullet: bool):
        p_pr = paragraph._p.get_or_add_pPr()
        for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buFont"):
            for el in p_pr.findall(qn(tag)):
                p_pr.remove(el)
        indent = Emu(342900)  # 0.375"
        if has_bullet:
            p_pr.set("marL", str(int(indent * (level + 1))))
            p_pr.set("indent", str(-int(Emu(285750))))
        else:
            p_pr.set("marL", str(int(indent * level)))
            p_pr.set("indent", "0")
        return p_pr

    def _set_bullet(self, paragraph, level: int) -> None:
        p_pr = self._reset_pPr(paragraph, level, has_bullet=True)
        bu_font = etree.SubElement(p_pr, qn("a:buFont"))
        bu_font.set("typeface", "Arial")
        bu_char = etree.SubElement(p_pr, qn("a:buChar"))
        bu_char.set("char", _BULLET_CHARS[level % 3])

    def _set_autonum(self, paragraph, level: int, start: int) -> None:
        p_pr = self._reset_pPr(paragraph, level, has_bullet=True)
        bu_num = etree.SubElement(p_pr, qn("a:buAutoNum"))
        bu_num.set("type", _AUTONUM_TYPES[level % 3])
        if start != 1:
            bu_num.set("startAt", str(start))

    def _set_no_bullet(self, paragraph, level: int) -> None:
        p_pr = self._reset_pPr(paragraph, level, has_bullet=False)
        etree.SubElement(p_pr, qn("a:buNone"))

    # ------------------------------------------------------------------ special slides
    def _add_title_slide(self, title: str) -> None:
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[_LAYOUT_TITLE])
        slide.shapes.title.text = title
        # Remove the empty subtitle placeholder so no "Click to add subtitle" remains.
        for shape in list(slide.placeholders):
            if shape.placeholder_format.idx == 0:
                continue
            if not shape.has_text_frame or not shape.text_frame.text.strip():
                shape._element.getparent().remove(shape._element)

    def _add_table_slides(self, block: TableBlock) -> None:
        cols = len(block.header)
        if cols == 0:
            return
        rows = block.rows or [[[] for _ in range(cols)]]
        chunks = [rows[i:i + MAX_TABLE_ROWS_PER_SLIDE] for i in range(0, len(rows), MAX_TABLE_ROWS_PER_SLIDE)]
        if cols > 8:
            self.warnings.append(f"Tabel {cols} kolom pada PPTX memakai font kecil agar muat di slide.")
        font_size = 14 if cols <= 5 else (12 if cols <= 8 else 10)

        for part, chunk in enumerate(chunks):
            title = self.current_title or "Tabel"
            slide = self._new_slide(f"{title} (lanjutan)" if part > 0 else title)
            n_rows = len(chunk) + 1
            row_h = 0.45
            shape = slide.shapes.add_table(
                n_rows,
                cols,
                Inches(BODY_LEFT_IN),
                Inches(BODY_TOP_IN),
                Inches(BODY_W_IN),
                Inches(min(BODY_H_IN, row_h * n_rows)),
            )
            table = shape.table
            for r_idx, row in enumerate([block.header, *chunk]):
                for c_idx in range(cols):
                    cell = table.cell(r_idx, c_idx)
                    cell_runs = row[c_idx] if c_idx < len(row) else []
                    tf = cell.text_frame
                    tf.word_wrap = True
                    paragraph = tf.paragraphs[0]
                    paragraph.alignment = _ALIGN_MAP.get(block.aligns[c_idx], PP_ALIGN.LEFT)
                    line = _Line(runs=cell_runs, size=font_size)
                    if r_idx == 0:
                        line.runs = [
                            InlineRun(**{**run.__dict__, "bold": True}) for run in cell_runs
                        ]
                    self._add_runs(paragraph, line)

    def _add_image_slide(self, block: ImageBlock) -> None:
        title = block.alt or self.current_title
        slide = self._new_slide(title)
        path = self.images.resolve(block.src)
        if path is None:
            box = slide.shapes.add_textbox(
                Inches(BODY_LEFT_IN), Inches(BODY_TOP_IN), Inches(BODY_W_IN), Inches(1)
            )
            run = box.text_frame.paragraphs[0].add_run()
            run.text = f"[Gambar tidak tersedia: {block.alt or block.src}]"
            run.font.italic = True
            run.font.size = Pt(18)
            return
        width_in, height_in = image_size_inches(path, max_width=BODY_W_IN, max_height=BODY_H_IN)
        left = Inches(BODY_LEFT_IN + (BODY_W_IN - width_in) / 2)
        top = Inches(BODY_TOP_IN + (BODY_H_IN - height_in) / 2)
        slide.shapes.add_picture(str(path), left, top, width=Inches(width_in), height=Inches(height_in))
