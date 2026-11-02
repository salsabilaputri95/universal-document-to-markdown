"""Render a parsed MarkdownDocument into a PDF file using ReportLab (pure local)."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import (
    ListItem as RLListItem,
)

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

PAGE_SIZES = {"A4": A4, "Letter": LETTER}
_ALIGN_MAP = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT}
_BULLET_CHARS = ["•", "◦", "▪"]
_ORDERED_TYPES = ["1", "a", "i"]

# Font families: (regular, bold, italic, bold-italic) file names
_SANS_CANDIDATES = [
    ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"),
    ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"),
]
_MONO_CANDIDATES = [
    ("consola.ttf", "consolab.ttf", "consolai.ttf", "consolaz.ttf"),
    ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf", "DejaVuSansMono-Oblique.ttf", "DejaVuSansMono-BoldOblique.ttf"),
]


def _font_dirs() -> list[Path]:
    dirs: list[Path] = []
    env_dir = os.environ.get("OMNIMARK_FONT_DIR")
    if env_dir:
        dirs.append(Path(env_dir))
    windir = os.environ.get("WINDIR")
    if windir:
        dirs.append(Path(windir) / "Fonts")
    dirs.extend(Path(p) for p in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"))
    return dirs


def _register_family(alias: str, candidates: list[tuple[str, str, str, str]]) -> bool:
    if alias in pdfmetrics.getRegisteredFontNames():
        return True
    for files in candidates:
        for font_dir in _font_dirs():
            paths = [font_dir / name for name in files]
            if not paths[0].is_file():
                continue
            # Missing style variants fall back to the regular face.
            resolved = [p if p.is_file() else paths[0] for p in paths]
            names = [alias, f"{alias}-Bold", f"{alias}-Italic", f"{alias}-BoldItalic"]
            try:
                for name, path in zip(names, resolved, strict=True):
                    pdfmetrics.registerFont(TTFont(name, str(path)))
                pdfmetrics.registerFontFamily(
                    alias, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3]
                )
                return True
            except Exception:  # noqa: BLE001 - try the next candidate font
                continue
    return False


def _resolve_fonts() -> tuple[str, str]:
    """Return (sans_family, mono_family). Falls back to built-in Helvetica/Courier."""
    sans = "OmniSans" if _register_family("OmniSans", _SANS_CANDIDATES) else "Helvetica"
    mono = "OmniMono" if _register_family("OmniMono", _MONO_CANDIDATES) else "Courier"
    return sans, mono


class PdfRenderer:
    """Render MarkdownDocument blocks as ReportLab flowables."""

    def __init__(self, image_resolver: ImageResolver | None = None, page_size: str = "A4"):
        self.images = image_resolver or ImageResolver()
        self.page_size = PAGE_SIZES.get(page_size, A4)
        self.warnings: list[str] = []
        self.sans, self.mono = _resolve_fonts()
        if self.sans == "Helvetica":
            self.warnings.append(
                "Font TTF sistem tidak ditemukan; memakai Helvetica bawaan (karakter non-Latin mungkin tidak tampil)."
            )
        self._build_styles()

    # ------------------------------------------------------------------ styles
    def _build_styles(self) -> None:
        base = getSampleStyleSheet()
        self.body = ParagraphStyle(
            "OmniBody", parent=base["BodyText"], fontName=self.sans, fontSize=10.5, leading=14.5, spaceAfter=6
        )
        heading_sizes = {1: 20, 2: 16, 3: 13.5, 4: 12, 5: 11, 6: 10.5}
        self.headings = {
            level: ParagraphStyle(
                f"OmniH{level}",
                parent=base[f"Heading{level}"],
                fontName=self.sans,
                fontSize=size,
                leading=size * 1.25,
                spaceBefore=12 if level <= 2 else 8,
                spaceAfter=6,
                textColor=colors.HexColor("#0F172A"),
            )
            for level, size in heading_sizes.items()
        }
        self.code = ParagraphStyle(
            "OmniCode",
            parent=self.body,
            fontName=self.mono,
            fontSize=9,
            leading=12,
            backColor=colors.HexColor("#F1F5F9"),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=10,
        )
        self.quote = ParagraphStyle(
            "OmniQuote",
            parent=self.body,
            leftIndent=18,
            textColor=colors.HexColor("#475569"),
            fontName=self.sans,
        )
        self.caption = ParagraphStyle("OmniCaption", parent=self.body, fontSize=9, alignment=TA_CENTER)
        self.cell_styles = {
            (align, header): ParagraphStyle(
                f"OmniCell-{align}-{header}",
                parent=self.body,
                fontSize=9.5,
                leading=12,
                spaceAfter=0,
                alignment=_ALIGN_MAP[align],
            )
            for align in _ALIGN_MAP
            for header in (True, False)
        }

    # ------------------------------------------------------------------ inline
    def _markup(self, runs: list[InlineRun], force_bold: bool = False) -> str:
        parts: list[str] = []
        for run in runs:
            if run.line_break:
                parts.append("<br/>")
                continue
            text = escape(run.text, quote=False)
            if run.code:
                text = f'<font face="{self.mono}" color="#B91C1C">{text}</font>'
            if run.strike:
                text = f"<strike>{text}</strike>"
            if run.italic:
                text = f"<i>{text}</i>"
            if run.bold or force_bold:
                text = f"<b>{text}</b>"
            if run.link:
                href = escape(run.link, quote=True)
                text = f'<a href="{href}" color="#2563EB"><u>{text}</u></a>'
            parts.append(text)
        return "".join(parts)

    # ------------------------------------------------------------------ render
    def render(self, doc_model: MarkdownDocument, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        margin = 2 * cm
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
            title=doc_model.title or "",
            creator="OmniMark",
        )
        self.avail_width = self.page_size[0] - 2 * margin
        self.avail_height = self.page_size[1] - 2 * margin

        story = []
        for block in doc_model.blocks:
            story.extend(self._block(block))
        if not story:
            story.append(Paragraph("", self.body))
        doc.build(story)
        self.warnings.extend(w for w in self.images.warnings if w not in self.warnings)
        return output_path

    def _block(self, block: Block, quote: bool = False) -> list:
        if isinstance(block, HeadingBlock):
            style = self.headings[min(max(block.level, 1), 6)]
            return [Paragraph(self._markup(block.runs), style)]
        if isinstance(block, ParagraphBlock):
            return [Paragraph(self._markup(block.runs), self.quote if quote else self.body)]
        if isinstance(block, ListBlock):
            return [self._list(block, level=0), Spacer(1, 4)]
        if isinstance(block, TableBlock):
            return self._table(block)
        if isinstance(block, CodeBlock):
            text = escape(block.code, quote=False).replace(" ", "&nbsp;").replace("\n", "<br/>")
            return [Paragraph(text or "&nbsp;", self.code)]
        if isinstance(block, QuoteBlock):
            flowables: list = []
            for inner in block.blocks:
                flowables.extend(self._block(inner, quote=True))
            return flowables
        if isinstance(block, HorizontalRuleBlock):
            return [
                HRFlowable(
                    width="100%",
                    thickness=0.8,
                    color=colors.HexColor("#CBD5E1"),
                    spaceBefore=6,
                    spaceAfter=6,
                )
            ]
        if isinstance(block, ImageBlock):
            return self._image(block)
        return []

    def _list(self, block: ListBlock, level: int) -> ListFlowable:
        items = []
        for item in block.items:
            flowables: list = [Paragraph(self._markup(item.runs) or "&nbsp;", self.body)]
            for child in item.children:
                if isinstance(child, ListBlock):
                    flowables.append(self._list(child, level + 1))
                else:
                    flowables.extend(self._block(child))
            items.append(RLListItem(flowables))

        common = {"leftIndent": 18, "bulletFontName": self.sans, "bulletFontSize": 10}
        if block.ordered:
            return ListFlowable(
                items,
                bulletType=_ORDERED_TYPES[level % 3],
                start=block.start,
                bulletFormat="%s.",
                **common,
            )
        return ListFlowable(items, bulletType="bullet", start=_BULLET_CHARS[level % 3], **common)

    def _table(self, block: TableBlock) -> list:
        cols = len(block.header)
        if cols == 0:
            return []
        data = []
        for row_idx, row in enumerate([block.header, *block.rows]):
            header = row_idx == 0
            data.append(
                [
                    Paragraph(self._markup(cell, force_bold=header), self.cell_styles[(block.aligns[c], header)])
                    for c, cell in enumerate(row)
                ]
            )
        col_width = self.avail_width / cols
        table = Table(data, colWidths=[col_width] * cols, repeatRows=1, hAlign="CENTER")
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        if cols > 8:
            self.warnings.append(f"Tabel dengan {cols} kolom dipersempit agar muat di lebar halaman PDF.")
        return [table, Spacer(1, 8)]

    def _image(self, block: ImageBlock) -> list:
        path = self.images.resolve(block.src)
        if path is None:
            return [Paragraph(f"<i>[Gambar tidak tersedia: {escape(block.alt or block.src)}]</i>", self.body)]
        width_in, height_in = image_size_inches(
            path, max_width=self.avail_width / inch, max_height=(self.avail_height / inch) * 0.8
        )
        flowables: list = [Image(str(path), width=width_in * inch, height=height_in * inch)]
        if block.alt:
            flowables.append(Paragraph(f"<i>{escape(block.alt)}</i>", self.caption))
        return flowables

