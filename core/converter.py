"""Conversion manager orchestrating file validation, engines, fallbacks, and markdown styling."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from core.docling_engine import DoclingEngine
from core.excel_processor import ExcelProcessor
from core.file_validator import FileValidator, ValidationResult
from core.markitdown_engine import MarkItDownEngine
from utils.file_utils import format_file_size, sanitize_filename
from utils.logger import logger
from utils.markdown_utils import count_markdown_stats, format_markdown_output


@dataclass
class ConversionResult:
    """Represents the outcome of a document conversion."""

    success: bool
    filename: str
    extension: str
    file_size_bytes: int
    file_size_formatted: str
    requested_engine: str
    used_engine: str
    markdown_content: str = ""
    output_md_path: Path | None = None
    asset_dir: Path | None = None
    extracted_images: list[dict[str, str]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error_message: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    converted_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ConversionManager:
    """Orchestrates conversion across multiple engines with automatic selection and fallback."""

    def __init__(
        self,
        ocr_enabled: bool = True,
        ocr_lang: str = "ind+eng",
        markdown_style: str = "standard",
        extract_images: bool = True,
    ):
        self.ocr_enabled = ocr_enabled
        self.ocr_lang = ocr_lang
        self.markdown_style = markdown_style
        self.extract_images = extract_images

        self._docling: DoclingEngine | None = None
        self._markitdown: MarkItDownEngine | None = None

    def get_docling(self) -> DoclingEngine:
        """Lazy load Docling engine."""
        if self._docling is None:
            self._docling = DoclingEngine(
                ocr_enabled=self.ocr_enabled,
                ocr_lang=self.ocr_lang,
                extract_images=self.extract_images,
            )
        return self._docling

    def get_markitdown(self) -> MarkItDownEngine:
        """Lazy load MarkItDown engine."""
        if self._markitdown is None:
            self._markitdown = MarkItDownEngine()
        return self._markitdown

    def convert_file(
        self,
        file_path: Path | str,
        engine_choice: str = "auto",
        output_dir: Path | None = None,
    ) -> ConversionResult:
        """Convert a single document file to markdown with validation and error isolation."""
        start_time = time.time()
        path = Path(file_path)
        out_dir = output_dir or settings.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Validation
        validation: ValidationResult = FileValidator.validate_file(path)
        if not validation.is_valid:
            duration = round(time.time() - start_time, 2)
            logger.warning(f"File validation failed for {path.name}: {validation.error_message}")
            return ConversionResult(
                success=False,
                filename=path.name,
                extension=validation.extension,
                file_size_bytes=validation.file_size_bytes,
                file_size_formatted=format_file_size(validation.file_size_bytes),
                requested_engine=engine_choice,
                used_engine="None",
                error_message=validation.error_message,
                duration_seconds=duration,
            )

        ext = validation.extension
        file_size_fmt = format_file_size(validation.file_size_bytes)

        # 2. Engine resolution
        chosen_engine = engine_choice.lower()
        if chosen_engine == "auto":
            if ext == ".xlsx":
                chosen_engine = "excel_processor"
            elif ext == ".csv":
                chosen_engine = "markitdown"
            elif ext in [".pdf", ".docx", ".pptx"]:
                chosen_engine = "docling"
            else:
                chosen_engine = "markitdown"

        markdown_text = ""
        meta_info: dict[str, Any] = {}
        extracted_images: list[dict[str, str]] = []
        fallback_used = False
        fallback_reason = None
        warnings: list[str] = []
        final_engine_name = chosen_engine

        # 3. Execution with fallback logic
        try:
            if chosen_engine == "excel_processor" or (chosen_engine == "auto" and ext == ".xlsx"):
                markdown_text, meta_info = ExcelProcessor.process_file(path)
                final_engine_name = "ExcelProcessor"
                warnings.extend(meta_info.get("warnings", []))

            elif chosen_engine == "docling":
                try:
                    markdown_text, meta_info, extracted_images = self.get_docling().convert(
                        file_path=path,
                        output_dir=out_dir,
                    )
                    final_engine_name = "Docling"
                except Exception as docling_err:
                    logger.warning(
                        f"Docling failed for {path.name}: {docling_err}. "
                        "Attempting fallback to MarkItDown."
                    )
                    fallback_used = True
                    fallback_reason = f"Docling error: {docling_err}"
                    # Fallback to MarkItDown
                    markdown_text, meta_info = self.get_markitdown().convert(path)
                    final_engine_name = "MarkItDown (Fallback)"

            elif chosen_engine == "markitdown":
                markdown_text, meta_info = self.get_markitdown().convert(path)
                final_engine_name = "MarkItDown"

            else:
                raise ValueError(f"Unknown conversion engine: {chosen_engine}")

        except Exception as conv_err:
            duration = round(time.time() - start_time, 2)
            error_str = f"Conversion error: {conv_err}"
            logger.error(f"Failed converting {path.name}: {conv_err}", exc_info=True)
            return ConversionResult(
                success=False,
                filename=path.name,
                extension=ext,
                file_size_bytes=validation.file_size_bytes,
                file_size_formatted=file_size_fmt,
                requested_engine=engine_choice,
                used_engine=final_engine_name,
                duration_seconds=duration,
                error_message=error_str,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
            )

        # 4. Format markdown output according to requested style
        meta_info["filename"] = path.name
        meta_info["extension"] = ext
        meta_info["file_size_formatted"] = file_size_fmt
        meta_info["engine"] = final_engine_name

        formatted_md = format_markdown_output(
            markdown_text=markdown_text,
            style=self.markdown_style,
            metadata=meta_info,
        )

        # 5. Save markdown output to file
        safe_stem = sanitize_filename(path.stem)
        output_file_name = f"{safe_stem}.md"
        output_md_path = out_dir / output_file_name
        output_md_path.write_text(formatted_md, encoding="utf-8")

        # 6. Asset folder
        asset_dir = None
        asset_folder_name = f"{safe_stem}_assets"
        potential_asset_dir = out_dir / asset_folder_name
        if potential_asset_dir.is_dir() and any(potential_asset_dir.iterdir()):
            asset_dir = potential_asset_dir

        stats = count_markdown_stats(formatted_md)
        duration = round(time.time() - start_time, 2)

        return ConversionResult(
            success=True,
            filename=path.name,
            extension=ext,
            file_size_bytes=validation.file_size_bytes,
            file_size_formatted=file_size_fmt,
            requested_engine=engine_choice,
            used_engine=final_engine_name,
            markdown_content=formatted_md,
            output_md_path=output_md_path,
            asset_dir=asset_dir,
            extracted_images=extracted_images,
            stats=stats,
            duration_seconds=duration,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            warnings=warnings,
        )

    def convert_batch(
        self,
        file_paths: list[Path | str],
        engine_choice: str = "auto",
        output_dir: Path | None = None,
        progress_callback: Any = None,
    ) -> list[ConversionResult]:
        """Convert a batch of files sequentially, isolating errors per file."""
        results: list[ConversionResult] = []
        total = len(file_paths)

        for index, file_p in enumerate(file_paths):
            if progress_callback:
                progress_callback(index, total, str(Path(file_p).name))

            result = self.convert_file(
                file_path=file_p,
                engine_choice=engine_choice,
                output_dir=output_dir,
            )
            results.append(result)

        if progress_callback:
            progress_callback(total, total, "Complete")

        return results
