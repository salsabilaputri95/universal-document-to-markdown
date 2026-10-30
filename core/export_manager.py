"""Export manager for generating standalone markdown files, metadata, and ZIP archives."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from core.converter import ConversionResult
from utils.file_utils import sanitize_filename
from utils.logger import logger
from utils.zip_utils import create_export_zip


class ExportManager:
    """Manages packaging and downloading of conversion results."""

    @classmethod
    def export_single_markdown(cls, result: ConversionResult) -> tuple[str, bytes]:
        """Prepare a single markdown file for download.

        Returns:
            Tuple of (filename, file_bytes)
        """
        stem = sanitize_filename(Path(result.filename).stem)
        filename = f"{stem}.md"
        return filename, result.markdown_content.encode("utf-8")

    @classmethod
    def export_metadata_json(cls, results: list[ConversionResult]) -> tuple[str, bytes]:
        """Export conversion results metadata as JSON."""
        metadata_payload = cls._build_metadata_payload(results)
        json_bytes = json.dumps(metadata_payload, indent=2, ensure_ascii=False).encode("utf-8")
        return "metadata.json", json_bytes

    @classmethod
    def create_batch_zip(
        cls,
        results: list[ConversionResult],
        zip_filename: str = "markdown-export.zip",
        output_dir: Path | None = None,
    ) -> Path:
        """Create a complete ZIP archive matching the required export structure.

        Returns:
            Path to the created ZIP archive.
        """
        out_dir = output_dir or settings.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / zip_filename

        markdown_files: dict[str, str] = {}
        asset_dirs: dict[str, Path] = {}

        # Collect successful conversion files
        for res in results:
            if res.success and res.markdown_content:
                stem = sanitize_filename(Path(res.filename).stem)
                md_name = f"{stem}.md"
                markdown_files[md_name] = res.markdown_content

                if res.asset_dir and res.asset_dir.is_dir():
                    asset_folder_name = f"{stem}_assets"
                    asset_dirs[asset_folder_name] = res.asset_dir

        metadata = cls._build_metadata_payload(results)

        success = create_export_zip(
            zip_dest_path=zip_path,
            markdown_files=markdown_files,
            asset_dirs=asset_dirs,
            metadata=metadata,
        )

        if not success:
            raise RuntimeError(f"Gagal membuat file ZIP di {zip_path}")

        logger.info(f"Successfully packaged {len(markdown_files)} documents into {zip_path.name}")
        return zip_path

    @classmethod
    def _build_metadata_payload(cls, results: list[ConversionResult]) -> dict[str, Any]:
        """Build structured metadata payload for export."""
        items = []
        for res in results:
            items.append({
                "filename": res.filename,
                "extension": res.extension,
                "file_size": res.file_size_formatted,
                "status": "success" if res.success else "failed",
                "requested_engine": res.requested_engine,
                "used_engine": res.used_engine,
                "fallback_used": res.fallback_used,
                "fallback_reason": res.fallback_reason,
                "stats": res.stats,
                "duration_seconds": res.duration_seconds,
                "warnings": res.warnings,
                "error_message": res.error_message,
                "converted_at": res.converted_at,
            })

        return {
            "application": "OmniMark",
            "tagline": "Universal Document to Markdown",
            "exported_at": datetime.now().isoformat(),
            "total_documents": len(results),
            "successful_conversions": sum(1 for r in results if r.success),
            "failed_conversions": sum(1 for r in results if not r.success),
            "documents": items,
        }
