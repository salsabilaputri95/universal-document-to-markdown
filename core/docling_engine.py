"""Docling conversion engine wrapper.

Provides CPU-friendly document conversion with OCR and image extraction support.
"""

from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    RapidOcrOptions,
    TesseractOcrOptions,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)

from config.settings import settings
from core.image_processor import ImageProcessor
from utils.logger import logger


class DoclingEngine:
    """Wrapper around Docling's DocumentConverter with CPU and OCR configurations."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".html"}

    def __init__(
        self,
        ocr_enabled: bool = True,
        ocr_lang: str = "ind+eng",
        extract_images: bool = True,
    ):
        self.ocr_enabled = ocr_enabled
        self.ocr_lang = ocr_lang
        self.extract_images = extract_images
        self._converter = self._build_converter()

    def _parse_ocr_langs(self) -> list[str]:
        """Convert 'ind+eng' or 'eng' into a list of language codes for OCR."""
        if "+" in self.ocr_lang:
            return [lang_code.strip() for lang_code in self.ocr_lang.split("+")]
        return [self.ocr_lang.strip()]

    def _build_converter(self) -> DocumentConverter:
        """Construct a DocumentConverter configured for local CPU execution."""
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = self.extract_images

        if self.ocr_enabled:
            pipeline_options.do_ocr = True
            langs = self._parse_ocr_langs()

            if settings.TESSERACT_CMD and Path(settings.TESSERACT_CMD).exists():
                try:
                    pipeline_options.ocr_options = TesseractOcrOptions(
                        path=settings.TESSERACT_CMD,
                        lang=langs,
                    )
                except Exception as err:
                    logger.warning(f"Could not initialize TesseractOcrOptions: {err}, falling back to RapidOcr")
                    pipeline_options.ocr_options = RapidOcrOptions()
            else:
                pipeline_options.ocr_options = RapidOcrOptions()
        else:
            pipeline_options.do_ocr = False

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }

        return DocumentConverter(format_options=format_options)

    def convert(
        self,
        file_path: Path | str,
        output_dir: Path | None = None,
    ) -> tuple[str, dict[str, Any], list[dict[str, str]]]:
        """Convert document using Docling.

        Returns:
            Tuple of (markdown_text, metadata, extracted_images_list)
        """
        path = Path(file_path)
        out_dir = output_dir or settings.OUTPUT_DIR
        stem = path.stem

        image_processor = ImageProcessor(base_output_dir=out_dir, doc_stem=stem)
        saved_images_info: list[dict[str, str]] = []

        try:
            conversion_res = self._converter.convert(path)
            doc = conversion_res.document

            # Extract pictures if requested
            if self.extract_images and hasattr(doc, "pictures"):
                for idx, pic in enumerate(doc.pictures):
                    try:
                        pil_img = pic.get_image(doc)
                        if pil_img:
                            caption = getattr(pic, "caption", "") or f"Figure {idx + 1}"
                            rel_path = image_processor.save_image(pil_img, image_format="PNG", caption=str(caption))
                            if rel_path:
                                saved_images_info.append({
                                    "filename": Path(rel_path).name,
                                    "relative_path": rel_path,
                                    "caption": str(caption),
                                })
                    except Exception as img_err:
                        logger.warning(f"Failed to extract image item {idx} from {path.name}: {img_err}")

            image_processor.clean_orphaned_asset_dir()

            # Export document to markdown
            markdown_content = doc.export_to_markdown()

            pages_count = getattr(doc, "num_pages", None)

            metadata: dict[str, Any] = {
                "filename": path.name,
                "engine": "Docling",
                "ocr_enabled": self.ocr_enabled,
                "ocr_lang": self.ocr_lang if self.ocr_enabled else None,
                "pages": pages_count,
                "extracted_images_count": len(saved_images_info),
            }

            return markdown_content, metadata, saved_images_info

        except Exception as err:
            logger.error(f"Docling conversion failed for {path.name}: {err}", exc_info=True)
            raise RuntimeError(f"Docling error: {err}") from err
