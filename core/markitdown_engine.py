"""Microsoft MarkItDown conversion engine wrapper."""

from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from utils.logger import logger


class MarkItDownEngine:
    """Wrapper around Microsoft MarkItDown library."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".csv"}

    def __init__(self):
        self._converter = MarkItDown()

    def convert(self, file_path: Path | str) -> tuple[str, dict[str, Any]]:
        """Convert a document to markdown using MarkItDown.

        Returns:
            Tuple of (markdown_text, metadata)
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            result = self._converter.convert(str(path))
            markdown_content = result.text_content or ""
            title = getattr(result, "title", None) or path.stem

            metadata: dict[str, Any] = {
                "filename": path.name,
                "engine": "Microsoft MarkItDown",
                "title": title,
            }

            return markdown_content, metadata

        except Exception as err:
            logger.error(f"MarkItDown conversion failed for {path.name}: {err}", exc_info=True)
            raise RuntimeError(f"MarkItDown error: {err}") from err
