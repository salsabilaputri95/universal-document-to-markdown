"""Markdown parser producing a renderer-agnostic document model.

The Markdown source is parsed once with markdown-it-py (CommonMark + GFM tables and
strikethrough) into a small block/inline model. The DOCX, PDF, and PPTX renderers all
consume this same model, so headings, numbering, bullets, tables, and inline
formatting are interpreted consistently across output formats.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from markdown_it import MarkdownIt
from markdown_it.token import Token

# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------


@dataclass
class InlineRun:
    """A span of text sharing the same inline formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    strike: bool = False
    code: bool = False
    link: str | None = None
    line_break: bool = False  # Hard line break (rendered as a new line, text is empty)


@dataclass
class HeadingBlock:
    level: int
    runs: list[InlineRun]


@dataclass
class ParagraphBlock:
    runs: list[InlineRun]


@dataclass
class ImageBlock:
    src: str
    alt: str = ""


@dataclass
class CodeBlock:
    code: str
    language: str = ""


@dataclass
class HorizontalRuleBlock:
    pass


@dataclass
class QuoteBlock:
    blocks: list[Block]


@dataclass
class ListItem:
    """A list item: the first paragraph's runs plus any nested blocks (e.g. sub-lists)."""

    runs: list[InlineRun]
    children: list[Block] = field(default_factory=list)


@dataclass
class ListBlock:
    ordered: bool
    items: list[ListItem]
    start: int = 1


@dataclass
class TableBlock:
    header: list[list[InlineRun]]
    rows: list[list[list[InlineRun]]]
    aligns: list[str]  # "left" | "center" | "right" per column


Block = (
    HeadingBlock
    | ParagraphBlock
    | ImageBlock
    | CodeBlock
    | HorizontalRuleBlock
    | QuoteBlock
    | ListBlock
    | TableBlock
)


@dataclass
class MarkdownDocument:
    blocks: list[Block]
    frontmatter: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def title(self) -> str | None:
        """Text of the first level-1 heading, if any."""
        for block in self.blocks:
            if isinstance(block, HeadingBlock) and block.level == 1:
                return runs_to_plain_text(block.runs).strip() or None
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"\A\s*<!--.*?-->\s*\Z", re.DOTALL)
_ALIGN_RE = re.compile(r"text-align:\s*(left|center|right)")


def runs_to_plain_text(runs: list[InlineRun]) -> str:
    """Flatten inline runs into plain text."""
    return "".join("\n" if r.line_break else r.text for r in runs)


def _split_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    """Strip a leading YAML frontmatter block (simple `key: value` lines only)."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return text, {}
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            if key.strip():
                meta[key.strip()] = value.strip()
    return text[match.end():], meta


def _parse_inline(token: Token, warnings: list[str]) -> list[InlineRun]:
    """Convert an `inline` token's children into formatted runs."""
    runs: list[InlineRun] = []
    bold = italic = strike = 0
    link_stack: list[str] = []

    def add(text: str, code: bool = False) -> None:
        if not text:
            return
        runs.append(
            InlineRun(
                text=text,
                bold=bold > 0,
                italic=italic > 0,
                strike=strike > 0,
                code=code,
                link=link_stack[-1] if link_stack else None,
            )
        )

    for child in token.children or []:
        t = child.type
        if t == "text":
            add(child.content)
        elif t == "code_inline":
            add(child.content, code=True)
        elif t == "strong_open":
            bold += 1
        elif t == "strong_close":
            bold = max(0, bold - 1)
        elif t == "em_open":
            italic += 1
        elif t == "em_close":
            italic = max(0, italic - 1)
        elif t == "s_open":
            strike += 1
        elif t == "s_close":
            strike = max(0, strike - 1)
        elif t == "link_open":
            link_stack.append(str(child.attrs.get("href", "")))
        elif t == "link_close":
            if link_stack:
                link_stack.pop()
        elif t == "softbreak":
            add(" ")
        elif t == "hardbreak":
            runs.append(InlineRun(text="", line_break=True))
        elif t == "image":
            # Image mixed with text: keep its alt text so no information is lost.
            alt = child.content or str(child.attrs.get("alt", ""))
            add(f"[Gambar: {alt}]" if alt else "[Gambar]")
        elif t == "html_inline":
            if not child.content.strip().startswith("<!--"):
                add(child.content)
        else:
            if child.content:
                add(child.content)
    return runs


def _image_only(token: Token) -> list[ImageBlock] | None:
    """Return image blocks if an inline token contains only images (and whitespace)."""
    children = token.children or []
    images: list[ImageBlock] = []
    for child in children:
        if child.type == "image":
            alt = child.content or str(child.attrs.get("alt", ""))
            images.append(ImageBlock(src=str(child.attrs.get("src", "")), alt=alt))
        elif child.type in ("softbreak", "hardbreak"):
            continue
        elif child.type == "text" and not child.content.strip():
            continue
        else:
            return None
    return images or None


def _find_close(tokens: list[Token], start: int) -> int:
    """Find the index of the matching close token for tokens[start] (nesting aware)."""
    level = tokens[start].level
    close_type = tokens[start].type.replace("_open", "_close")
    for idx in range(start + 1, len(tokens)):
        if tokens[idx].type == close_type and tokens[idx].level == level:
            return idx
    return len(tokens) - 1


def _parse_table(tokens: list[Token], warnings: list[str]) -> TableBlock:
    header: list[list[InlineRun]] = []
    rows: list[list[list[InlineRun]]] = []
    aligns: list[str] = []
    current_row: list[list[InlineRun]] = []
    in_head = False

    for idx, tok in enumerate(tokens):
        if tok.type == "thead_open":
            in_head = True
        elif tok.type == "thead_close":
            in_head = False
        elif tok.type == "tr_open":
            current_row = []
        elif tok.type in ("th_open", "td_open"):
            if in_head:
                style = str(tok.attrs.get("style", ""))
                match = _ALIGN_RE.search(style)
                aligns.append(match.group(1) if match else "left")
            nxt = tokens[idx + 1] if idx + 1 < len(tokens) else None
            current_row.append(_parse_inline(nxt, warnings) if nxt and nxt.type == "inline" else [])
        elif tok.type == "tr_close":
            if in_head:
                header = current_row
            else:
                rows.append(current_row)

    col_count = max([len(header)] + [len(r) for r in rows] + [0])
    header = header + [[] for _ in range(col_count - len(header))]
    rows = [r + [[] for _ in range(col_count - len(r))] for r in rows]
    aligns = aligns + ["left"] * (col_count - len(aligns))
    return TableBlock(header=header, rows=rows, aligns=aligns)


def _parse_list_item(tokens: list[Token], warnings: list[str]) -> ListItem:
    """Parse tokens between list_item_open and list_item_close (exclusive)."""
    blocks = _parse_blocks(tokens, warnings)
    if blocks and isinstance(blocks[0], ParagraphBlock):
        return ListItem(runs=blocks[0].runs, children=blocks[1:])
    return ListItem(runs=[], children=blocks)


def _parse_blocks(tokens: list[Token], warnings: list[str]) -> list[Block]:
    blocks: list[Block] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        t = tok.type

        if t == "heading_open":
            level = int(tok.tag[1]) if tok.tag[1:].isdigit() else 1
            inline = tokens[i + 1]
            blocks.append(HeadingBlock(level=level, runs=_parse_inline(inline, warnings)))
            i = _find_close(tokens, i) + 1

        elif t == "paragraph_open":
            inline = tokens[i + 1]
            images = _image_only(inline)
            if images:
                blocks.extend(images)
            else:
                runs = _parse_inline(inline, warnings)
                if runs:
                    blocks.append(ParagraphBlock(runs=runs))
            i = _find_close(tokens, i) + 1

        elif t in ("bullet_list_open", "ordered_list_open"):
            close = _find_close(tokens, i)
            ordered = t == "ordered_list_open"
            start = int(tok.attrs.get("start", 1)) if ordered else 1
            items: list[ListItem] = []
            j = i + 1
            while j < close:
                if tokens[j].type == "list_item_open":
                    item_close = _find_close(tokens, j)
                    items.append(_parse_list_item(tokens[j + 1:item_close], warnings))
                    j = item_close + 1
                else:
                    j += 1
            blocks.append(ListBlock(ordered=ordered, items=items, start=start))
            i = close + 1

        elif t in ("fence", "code_block"):
            language = (tok.info or "").strip().split(" ")[0] if t == "fence" else ""
            blocks.append(CodeBlock(code=tok.content.rstrip("\n"), language=language))
            i += 1

        elif t == "blockquote_open":
            close = _find_close(tokens, i)
            blocks.append(QuoteBlock(blocks=_parse_blocks(tokens[i + 1:close], warnings)))
            i = close + 1

        elif t == "table_open":
            close = _find_close(tokens, i)
            blocks.append(_parse_table(tokens[i + 1:close], warnings))
            i = close + 1

        elif t == "hr":
            blocks.append(HorizontalRuleBlock())
            i += 1

        elif t == "html_block":
            content = tok.content.strip()
            if content and not _HTML_COMMENT_RE.match(content):
                # Raw HTML is not interpreted; keep it as literal text so nothing is lost.
                blocks.append(ParagraphBlock(runs=[InlineRun(text=content, code=True)]))
                warnings.append("Blok HTML mentah tidak dirender dan disertakan sebagai teks biasa.")
            i += 1

        else:
            i += 1
    return blocks


def parse_markdown(text: str) -> MarkdownDocument:
    """Parse Markdown text into a MarkdownDocument."""
    warnings: list[str] = []
    body, frontmatter = _split_frontmatter(text.replace("\r\n", "\n"))
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    tokens = md.parse(body)
    blocks = _parse_blocks(tokens, warnings)
    # De-duplicate warnings while keeping order
    unique_warnings = list(dict.fromkeys(warnings))
    return MarkdownDocument(blocks=blocks, frontmatter=frontmatter, warnings=unique_warnings)

