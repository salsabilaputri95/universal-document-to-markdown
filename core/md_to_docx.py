"""Render a parsed MarkdownDocument into a Microsoft Word (.docx) file."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

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
)
from core.md_render_common import ImageResolver, image_size_inches

MONO_FONT = "Consolas"
_ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
}
_BULLET_CHARS = ["•", "◦", "▪"]
_ORDERED_FORMATS = [("decimal", "%{n}."), ("lowerLetter", "%{n}."), ("lowerRoman", "%{n}.")]


class _Numbering:
    """Creates real Word numbering definitions (not typed '1.' text).

    One bullet definition is shared; every ordered list gets its own numbering
    instance so numbering restarts at the list's start value.
    """

    def __init__(self, document):
        self._numbering = document.part.numbering_part.element
        self._bullet_abstract = self._add_abstract(ordered=False)
        self._ordered_abstract = self._add_abstract(ordered=True)
        self._bullet_num: int | None = None

    def _next_id(self, xpath: str, attr: str) -> int:
        ids = [int(el.get(qn(attr))) for el in self._numbering.findall(qn(xpath))]
        return max(ids, default=0) + 1

    def _add_abstract(self, ordered: bool) -> int:
        abstract_id = self._next_id("w:abstractNum", "w:abstractNumId")
        levels = []
        for lvl in range(9):
            left = 720 * (lvl + 1)
            if ordered:
                fmt, text = _ORDERED_FORMATS[lvl % 3]
                lvl_text = text.format(n=lvl + 1)
                levels.append(
                    f'<w:lvl w:ilvl="{lvl}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/>'
                    f'<w:lvlText w:val="{lvl_text}"/><w:lvlJc w:val="left"/>'
                    f'<w:pPr><w:ind w:left="{left}" w:hanging="360"/></w:pPr></w:lvl>'
                )
            else:
                char = _BULLET_CHARS[lvl % 3]
                levels.append(
                    f'<w:lvl w:ilvl="{lvl}"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
                    f'<w:lvlText w:val="{char}"/><w:lvlJc w:val="left"/>'
                    f'<w:pPr><w:ind w:left="{left}" w:hanging="360"/></w:pPr></w:lvl>'
                )
        xml = (
            f'<w:abstractNum {nsdecls("w")} w:abstractNumId="{abstract_id}">'
            '<w:multiLevelType w:val="hybridMultilevel"/>' + "".join(levels) + "</w:abstractNum>"
        )
        element = parse_xml(xml)
        # Schema order: all abstractNum elements must precede num elements.
        first_num = self._numbering.find(qn("w:num"))
        if first_num is not None:
            first_num.addprevious(element)
        else:
            self._numbering.append(element)
        return abstract_id

    def _add_num(self, abstract_id: int, start: int | None = None) -> int:
        num_id = self._next_id("w:num", "w:numId")
        override = (
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="{start}"/></w:lvlOverride>'
            if start is not None
            else ""
        )
        xml = (
            f'<w:num {nsdecls("w")} w:numId="{num_id}">'
            f'<w:abstractNumId w:val="{abstract_id}"/>{override}</w:num>'
        )
        self._numbering.append(parse_xml(xml))
        return num_id

    def bullet_num(self) -> int:
        if self._bullet_num is None:
            self._bullet_num = self._add_num(self._bullet_abstract)
        return self._bullet_num

    def new_ordered_num(self, start: int) -> int:
        return self._add_num(self._ordered_abstract, start=start)


def _apply_numbering(paragraph, num_id: int, level: int) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = p_pr.get_or_add_numPr()
    num_pr.get_or_add_ilvl().val = min(level, 8)
    num_pr.get_or_add_numId().val = num_id


def _shade_paragraph(paragraph, fill: str = "F1F5F9") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill}"/>'))


def _add_bottom_border(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.append(
        parse_xml(
            f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr>'
        )
    )


def _mark_header_row(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


class DocxRenderer:
    """Render MarkdownDocument blocks into a python-docx Document."""

    def __init__(self, image_resolver: ImageResolver | None = None):
        self.images = image_resolver or ImageResolver()
        self.warnings: list[str] = []

    def render(self, doc_model: MarkdownDocument, output_path: Path) -> Path:
        self.document = Document()
        self.numbering = _Numbering(self.document)
        self._set_base_styles()

        title = doc_model.title or doc_model.frontmatter.get("source_file")
        if title:
            self.document.core_properties.title = title

        for block in doc_model.blocks:
            self._render_block(block, list_level=0)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.document.save(output_path)
        self.warnings.extend(w for w in self.images.warnings if w not in self.warnings)
        return output_path

    # ------------------------------------------------------------------ styles
    def _set_base_styles(self) -> None:
        normal = self.document.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)

    # ------------------------------------------------------------------ inline
    def _add_runs(self, paragraph, runs: list[InlineRun], force_bold: bool = False) -> None:
        for run_model in runs:
            if run_model.line_break:
                paragraph.add_run().add_break()
                continue
            if run_model.link:
                self._add_hyperlink(paragraph, run_model, force_bold)
                continue
            run = paragraph.add_run(run_model.text)
            self._format_run(run, run_model, force_bold)

    @staticmethod
    def _format_run(run, model: InlineRun, force_bold: bool = False) -> None:
        run.bold = model.bold or force_bold or None
        run.italic = model.italic or None
        if model.strike:
            run.font.strike = True
        if model.code:
            run.font.name = MONO_FONT
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C)

    def _add_hyperlink(self, paragraph, model: InlineRun, force_bold: bool) -> None:
        r_id = paragraph.part.relate_to(model.link, RT.HYPERLINK, is_external=True)
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)
        # Build the run through python-docx so formatting helpers apply, then move it.
        temp_run = paragraph.add_run(model.text)
        self._format_run(temp_run, model, force_bold)
        temp_run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
        temp_run.font.underline = True
        hyperlink.append(temp_run._r)
        paragraph._p.append(hyperlink)

    # ------------------------------------------------------------------ blocks
    def _render_block(self, block: Block, list_level: int, quote: bool = False) -> None:
        if isinstance(block, HeadingBlock):
            heading = self.document.add_heading(level=min(max(block.level, 1), 9))
            self._add_runs(heading, block.runs)
        elif isinstance(block, ParagraphBlock):
            paragraph = self.document.add_paragraph(style="Quote" if quote else None)
            self._add_runs(paragraph, block.runs)
        elif isinstance(block, ListBlock):
            self._render_list(block, list_level)
        elif isinstance(block, TableBlock):
            self._render_table(block)
        elif isinstance(block, CodeBlock):
            self._render_code(block)
        elif isinstance(block, QuoteBlock):
            for inner in block.blocks:
                self._render_block(inner, list_level, quote=True)
        elif isinstance(block, HorizontalRuleBlock):
            _add_bottom_border(self.document.add_paragraph())
        elif isinstance(block, ImageBlock):
            self._render_image(block)

    def _render_list(self, block: ListBlock, level: int) -> None:
        num_id = (
            self.numbering.new_ordered_num(block.start) if block.ordered else self.numbering.bullet_num()
        )
        for item in block.items:
            paragraph = self.document.add_paragraph()
            _apply_numbering(paragraph, num_id, level)
            paragraph.paragraph_format.space_after = Pt(2)
            self._add_runs(paragraph, item.runs)
            for child in item.children:
                if isinstance(child, ListBlock):
                    self._render_list(child, level + 1)
                elif isinstance(child, ParagraphBlock):
                    extra = self.document.add_paragraph()
                    extra.paragraph_format.left_indent = Inches(0.5 * (level + 1))
                    self._add_runs(extra, child.runs)
                else:
                    self._render_block(child, level + 1)

    def _render_table(self, block: TableBlock) -> None:
        cols = len(block.header)
        if cols == 0:
            return
        table = self.document.add_table(rows=1 + len(block.rows), cols=cols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for row_idx, row_cells in enumerate([block.header, *block.rows]):
            row = table.rows[row_idx]
            for col_idx, cell_runs in enumerate(row_cells):
                cell = row.cells[col_idx]
                paragraph = cell.paragraphs[0]
                paragraph.alignment = _ALIGN_MAP.get(block.aligns[col_idx], WD_ALIGN_PARAGRAPH.LEFT)
                self._add_runs(paragraph, cell_runs, force_bold=row_idx == 0)
                if row_idx == 0:
                    cell._tc.get_or_add_tcPr().append(
                        parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="E2E8F0"/>')
                    )
        _mark_header_row(table.rows[0])
        self.document.add_paragraph()  # spacing after table

    def _render_code(self, block: CodeBlock) -> None:
        paragraph = self.document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(6)
        _shade_paragraph(paragraph)
        lines = block.code.split("\n")
        for idx, line in enumerate(lines):
            run = paragraph.add_run(line)
            run.font.name = MONO_FONT
            run.font.size = Pt(9.5)
            if idx < len(lines) - 1:
                run.add_break()

    def _render_image(self, block: ImageBlock) -> None:
        path = self.images.resolve(block.src)
        if path is None:
            paragraph = self.document.add_paragraph()
            run = paragraph.add_run(f"[Gambar tidak tersedia: {block.alt or block.src}]")
            run.italic = True
            run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            return
        width, _ = image_size_inches(path, max_width=6.0, max_height=8.0)
        self.document.add_picture(str(path), width=Inches(width))
        self.document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if block.alt:
            caption = self.document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = caption.add_run(block.alt)
            run.italic = True
            run.font.size = Pt(9)

