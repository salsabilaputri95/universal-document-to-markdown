"""Markdown -> DOCX / PDF / PPTX export orchestration."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config.settings import settings
from core.md_parser import MarkdownDocument, parse_markdown
from core.md_render_common import ImageResolver
from core.md_to_docx import DocxRenderer
from core.md_to_pdf import PdfRenderer
from core.md_to_pptx import PptxRenderer
from utils.file_utils import format_file_size, sanitize_filename
from utils.logger import logger

FORMAT_LABELS = {
    "docx": "Microsoft Word (.docx)",
    "pdf": "PDF (.pdf)",
    "pptx": "Microsoft PowerPoint (.pptx)",
}
FORMAT_MIME = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


@dataclass
class ExportFileResult:
    """Outcome of exporting one Markdown source into one target format."""

    format: str
    success: bool
    output_path: Path | None = None
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    file_size_bytes: int = 0

    @property
    def file_size_formatted(self) -> str:
        return format_file_size(self.file_size_bytes)


@dataclass
class MarkdownExportResult:
    """Outcome of exporting one Markdown source into all requested formats."""

    source_name: str
    files: list[ExportFileResult] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    exported_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def success_count(self) -> int:
        return sum(1 for f in self.files if f.success)


class MarkdownExporter:
    """Convert Markdown text/files into Word, PDF, and PowerPoint documents."""

    def __init__(self, page_size: str = "A4", slide_split_level: int = 2):
        self.page_size = page_size
        self.slide_split_level = slide_split_level

    # ------------------------------------------------------------------ input
    @staticmethod
    def load_markdown_file(path: Path | str) -> tuple[str, list[str]]:
        """Validate and read a Markdown file. Raises ValueError with a user-facing message."""
        path = Path(path)
        if not path.is_file():
            raise ValueError(f"File tidak ditemukan: {path.name}")
        if path.suffix.lower() not in settings.MARKDOWN_EXTENSIONS:
            allowed = ", ".join(settings.MARKDOWN_EXTENSIONS)
            raise ValueError(f"Format '{path.suffix}' tidak didukung. Gunakan: {allowed}")
        size = path.stat().st_size
        if size == 0:
            raise ValueError(f"File '{path.name}' kosong (0 byte).")
        if size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Ukuran file '{path.name}' melebihi {settings.MAX_FILE_SIZE_MB} MB.")

        raw = path.read_bytes()
        if b"\x00" in raw[:8192]:
            raise ValueError(f"File '{path.name}' terdeteksi sebagai file biner, bukan teks Markdown.")
        warnings: list[str] = []
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
            warnings.append("File bukan UTF-8 valid; karakter yang tidak terbaca diganti dengan '�'.")
        if not text.strip():
            raise ValueError(f"File '{path.name}' tidak berisi teks.")
        return text, warnings

    # ------------------------------------------------------------------ export
    def export_text(
        self,
        markdown_text: str,
        base_name: str,
        formats: list[str],
        output_dir: Path | None = None,
        base_dirs: list[Path] | None = None,
        extra_images: dict[str, Path] | None = None,
        extra_warnings: list[str] | None = None,
    ) -> MarkdownExportResult:
        """Export Markdown text to each requested format, isolating failures per format."""
        out_dir = output_dir or settings.MD_EXPORT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(sanitize_filename(f"{Path(base_name).stem or 'dokumen'}.md")).stem
        result = MarkdownExportResult(source_name=base_name, parse_warnings=list(extra_warnings or []))

        if not markdown_text.strip():
            result.error_message = "Teks Markdown kosong."
            return result

        try:
            doc_model = parse_markdown(markdown_text)
        except Exception as err:  # noqa: BLE001 - surfaced to the user, batch continues
            logger.error(f"Markdown parse failed for {base_name}: {err}", exc_info=True)
            result.error_message = f"Gagal mem-parsing Markdown: {err}"
            return result
        result.parse_warnings.extend(doc_model.warnings)

        for fmt in formats:
            result.files.append(
                self._export_one(doc_model, fmt, out_dir / f"{stem}.{fmt}", stem, base_dirs, extra_images)
            )
        return result

    def export_file(
        self,
        path: Path | str,
        formats: list[str],
        output_dir: Path | None = None,
        extra_images: dict[str, Path] | None = None,
    ) -> MarkdownExportResult:
        path = Path(path)
        try:
            text, warnings = self.load_markdown_file(path)
        except ValueError as err:
            return MarkdownExportResult(source_name=path.name, error_message=str(err))
        return self.export_text(
            text,
            base_name=path.name,
            formats=formats,
            output_dir=output_dir,
            base_dirs=[path.parent],
            extra_images=extra_images,
            extra_warnings=warnings,
        )

    def _export_one(
        self,
        doc_model: MarkdownDocument,
        fmt: str,
        target: Path,
        stem: str,
        base_dirs: list[Path] | None,
        extra_images: dict[str, Path] | None,
    ) -> ExportFileResult:
        start = time.time()
        resolver = ImageResolver(base_dirs=base_dirs, extra_images=extra_images)
        try:
            if fmt == "docx":
                renderer = DocxRenderer(image_resolver=resolver)
                renderer.render(doc_model, target)
            elif fmt == "pdf":
                renderer = PdfRenderer(image_resolver=resolver, page_size=self.page_size)
                renderer.render(doc_model, target)
            elif fmt == "pptx":
                renderer = PptxRenderer(image_resolver=resolver, split_level=self.slide_split_level)
                renderer.render(doc_model, target, fallback_title=stem)
            else:
                raise ValueError(f"Format output tidak didukung: {fmt}")
        except Exception as err:  # noqa: BLE001 - one format failing must not stop the others
            logger.error(f"Markdown export to {fmt} failed for {stem}: {err}", exc_info=True)
            return ExportFileResult(
                format=fmt,
                success=False,
                error_message=str(err),
                duration_seconds=round(time.time() - start, 2),
            )
        return ExportFileResult(
            format=fmt,
            success=True,
            output_path=target,
            warnings=list(renderer.warnings),
            duration_seconds=round(time.time() - start, 2),
            file_size_bytes=target.stat().st_size,
        )

