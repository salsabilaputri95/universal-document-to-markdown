"""Shared helpers for Markdown -> DOCX/PDF/PPTX renderers."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

from utils.file_utils import is_safe_path

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}


class ImageResolver:
    """Resolve Markdown image references to local files only.

    - Remote URLs (http/https/data) are never downloaded (local-first policy).
    - Relative paths are resolved against the given base directories and must stay
      inside them (path traversal protection).
    - As a fallback, the file name is matched against separately uploaded images,
      so `doc_assets/image_001.png` resolves to an uploaded `image_001.png`.
    """

    def __init__(
        self,
        base_dirs: list[Path] | None = None,
        extra_images: dict[str, Path] | None = None,
    ):
        self.base_dirs = [Path(d) for d in (base_dirs or [])]
        self.extra_images = {k.lower(): Path(v) for k, v in (extra_images or {}).items()}
        self.warnings: list[str] = []
        self._cache: dict[str, Path | None] = {}

    def _warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def resolve(self, src: str) -> Path | None:
        if src in self._cache:
            return self._cache[src]
        result = self._resolve(src)
        self._cache[src] = result
        return result

    def _resolve(self, src: str) -> Path | None:
        if not src:
            return None
        parsed = urlparse(src)
        if parsed.scheme in ("http", "https", "data", "ftp"):
            self._warn(f"Gambar remote tidak diunduh (kebijakan lokal): {src[:80]}")
            return None

        rel = unquote(parsed.path).replace("\\", "/")
        if Path(rel).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            self._warn(f"Format gambar tidak didukung: {src}")
            return None

        for base in self.base_dirs:
            candidate = base / rel
            if is_safe_path(base, candidate) and candidate.is_file() and self._is_valid_image(candidate):
                return candidate

        by_name = self.extra_images.get(Path(rel).name.lower())
        if by_name and by_name.is_file() and self._is_valid_image(by_name):
            return by_name

        self._warn(f"Gambar tidak ditemukan: {src}")
        return None

    @staticmethod
    def _is_valid_image(path: Path) -> bool:
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except Exception:  # noqa: BLE001 - any decode failure means "not a usable image"
            return False


def image_size_inches(path: Path, max_width: float, max_height: float | None = None) -> tuple[float, float]:
    """Return (width, height) in inches, scaled down to fit the limits (never upscaled)."""
    with Image.open(path) as img:
        w_px, h_px = img.size
        dpi = img.info.get("dpi", (96, 96))
    dpi_x = float(dpi[0]) if dpi and dpi[0] else 96.0
    dpi_y = float(dpi[1]) if dpi and len(dpi) > 1 and dpi[1] else dpi_x
    width = w_px / dpi_x
    height = h_px / dpi_y
    scale = min(1.0, max_width / width if width else 1.0)
    if max_height:
        scale = min(scale, max_height / height if height else 1.0)
    return width * scale, height * scale

