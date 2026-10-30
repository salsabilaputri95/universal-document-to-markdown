"""Image extraction, naming, and markdown reference management."""

import io
from pathlib import Path

from PIL import Image

from utils.file_utils import sanitize_filename
from utils.logger import logger


class ImageProcessor:
    """Handles saving, indexing, and linking extracted images."""

    def __init__(self, base_output_dir: Path, doc_stem: str):
        self.base_output_dir = base_output_dir
        self.doc_stem = sanitize_filename(doc_stem)
        self.asset_folder_name = f"{self.doc_stem}_assets"
        self.asset_dir = self.base_output_dir / self.asset_folder_name
        self.saved_images: list[dict[str, str]] = []
        self._image_counter = 0

    def ensure_asset_dir(self) -> Path:
        """Create asset directory on demand."""
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        return self.asset_dir

    def save_image(
        self,
        image_data: bytes | Image.Image,
        image_format: str = "PNG",
        caption: str = "",
    ) -> str | None:
        """Save an image to the asset directory and return its markdown relative path.

        Returns None if image data is invalid.
        """
        self.ensure_asset_dir()
        self._image_counter += 1
        filename = f"image_{self._image_counter:03d}.{image_format.lower()}"
        target_path = self.asset_dir / filename

        try:
            if isinstance(image_data, bytes):
                # Validate image bytes with PIL
                with Image.open(io.BytesIO(image_data)) as img:
                    img.save(target_path, format=image_format.upper())
            elif isinstance(image_data, Image.Image):
                image_data.save(target_path, format=image_format.upper())
            else:
                logger.warning(f"Unsupported image data type: {type(image_data)}")
                return None

            # Verify saved file exists and has size
            if not target_path.is_file() or target_path.stat().st_size == 0:
                logger.warning(f"Saved image file is empty or missing: {target_path}")
                return None

            # Windows-compatible relative path using forward slashes for Markdown standard
            relative_path = f"{self.asset_folder_name}/{filename}"
            self.saved_images.append({
                "filename": filename,
                "relative_path": relative_path,
                "absolute_path": str(target_path),
                "caption": caption,
            })
            return relative_path

        except Exception as err:
            logger.error(f"Failed to save image {filename}: {err}")
            return None

    def get_markdown_tag(self, relative_path: str, caption: str = "") -> str:
        """Generate markdown image tag."""
        alt_text = caption.strip() or f"Image {self._image_counter}"
        return f"![{alt_text}]({relative_path})"

    def clean_orphaned_asset_dir(self) -> None:
        """Remove asset directory if no images were actually saved."""
        if self.asset_dir.exists() and not self.saved_images:
            try:
                # Only delete if directory is empty
                if not any(self.asset_dir.iterdir()):
                    self.asset_dir.rmdir()
            except Exception as err:
                logger.warning(f"Could not remove empty asset directory {self.asset_dir}: {err}")

