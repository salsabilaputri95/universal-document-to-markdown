"""ZIP archiving utilities for document and asset bundles."""

import json
import zipfile
from pathlib import Path
from typing import Any

from utils.logger import logger


def create_export_zip(
    zip_dest_path: Path,
    markdown_files: dict[str, str],
    asset_dirs: dict[str, Path] | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Create a ZIP archive containing converted markdown files, image asset directories, and metadata.json.

    Args:
        zip_dest_path: Path where the ZIP file will be saved.
        markdown_files: Dictionary mapping file name (e.g. 'report.md') to markdown string content.
        asset_dirs: Dictionary mapping asset folder name (e.g. 'report_assets') to local directory Path.
        metadata: Optional metadata dictionary saved as metadata.json in the ZIP root.

    Returns:
        True if successful, False otherwise.
    """
    try:
        zip_dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Write markdown files
            for md_name, md_content in markdown_files.items():
                # Normalize filename without subdirectories
                safe_name = Path(md_name).name
                zf.writestr(safe_name, md_content.encode("utf-8"))

            # 2. Write asset directories if any
            if asset_dirs:
                for asset_folder_name, local_dir in asset_dirs.items():
                    if local_dir and local_dir.is_dir():
                        for asset_file in local_dir.glob("*"):
                            if asset_file.is_file():
                                archive_rel_path = f"{asset_folder_name}/{asset_file.name}"
                                zf.write(asset_file, arcname=archive_rel_path)

            # 3. Write metadata.json
            if metadata is not None:
                meta_json = json.dumps(metadata, indent=2, ensure_ascii=False)
                zf.writestr("metadata.json", meta_json.encode("utf-8"))

        return True
    except Exception as err:
        logger.error(f"Failed to create ZIP package at {zip_dest_path}: {err}", exc_info=True)
        return False


def verify_zip_integrity(zip_path: Path) -> tuple[bool, str]:
    """Test ZIP file integrity and report if it's valid."""
    if not zip_path.is_file():
        return False, "File does not exist."
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                return False, f"Corrupted file inside archive: {bad_file}"
        return True, "Valid ZIP file."
    except Exception as err:
        return False, f"ZIP read error: {err}"

