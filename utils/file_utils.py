"""File utilities for path sanitization, size calculation, and temporary directory management."""

import re
import shutil
import uuid
from pathlib import Path

from config.settings import settings
from utils.logger import logger

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename(filename: str, fallback_stem: str = "document") -> str:
    """Sanitize a filename for Windows file system safety.

    Strips reserved characters (<>:"/\\|?*), prevents path traversal,
    and handles Windows reserved device names.
    """
    raw_path = Path(filename)
    stem = raw_path.stem.strip()
    ext = raw_path.suffix.strip().lower()

    # Remove illegal characters for Windows filenames
    clean_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem)
    # Collapse consecutive underscores and dots
    clean_stem = re.sub(r"[_\.\s]+", "_", clean_stem).strip("._ ")

    if not clean_stem or clean_stem.upper() in WINDOWS_RESERVED_NAMES:
        clean_stem = f"{fallback_stem}_{uuid.uuid4().hex[:6]}"

    # Cap stem length to prevent MAX_PATH issues on Windows
    clean_stem = clean_stem[:120]

    return f"{clean_stem}{ext}"


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Check if target_path is strictly inside base_dir to prevent path traversal."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return (
            resolved_target == resolved_base
            or resolved_base in resolved_target.parents
        )
    except Exception as err:
        logger.warning(f"Path safety check error for {target_path}: {err}")
        return False


def format_file_size(size_in_bytes: int) -> str:
    """Return a human-readable representation of a file size."""
    if size_in_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_in_bytes)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.2f} {units[unit_index]}"


def create_isolated_temp_dir(prefix: str = "job_") -> Path:
    """Create a temporary directory dedicated to a specific job or file."""
    unique_name = f"{prefix}{uuid.uuid4().hex[:8]}"
    temp_path = settings.TEMP_DIR / unique_name
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def cleanup_directory(directory_path: Path | str) -> bool:
    """Safely delete a directory and its contents."""
    path = Path(directory_path)
    if not path.exists():
        return True
    try:
        shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception as err:
        logger.warning(f"Failed to cleanup directory {path}: {err}")
        return False

