"""Application configuration and settings."""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppSettings:
    """Central configuration for OmniMark (Universal Document to Markdown)."""

    APP_NAME: str = "OmniMark"
    APP_VERSION: str = "1.0.0"

    # Project directories
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    INPUT_DIR: Path = field(init=False)
    OUTPUT_DIR: Path = field(init=False)
    TEMP_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)

    # File handling
    MAX_FILE_SIZE_MB: int = 100
    SUPPORTED_EXTENSIONS: list[str] = field(
        default_factory=lambda: [".pdf", ".docx", ".xlsx", ".pptx", ".csv"]
    )
    MIME_TYPES: dict[str, list[str]] = field(
        default_factory=lambda: {
            ".pdf": ["application/pdf"],
            ".docx": [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "application/zip",
            ],
            ".xlsx": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/zip",
            ],
            ".pptx": [
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.ms-powerpoint",
                "application/zip",
            ],
            ".csv": ["text/csv", "text/plain", "application/csv"],
        }
    )

    # Conversion settings
    DEFAULT_ENGINE: str = "auto"  # 'docling', 'markitdown', 'auto'
    AVAILABLE_ENGINES: list[str] = field(
        default_factory=lambda: ["auto", "docling", "markitdown"]
    )

    # Markdown styles
    MARKDOWN_STYLES: list[str] = field(
        default_factory=lambda: ["standard", "with_metadata", "with_images", "rag"]
    )

    # OCR settings
    OCR_ENABLED: bool = True
    DEFAULT_OCR_LANG: str = "ind+eng"
    SUPPORTED_OCR_LANGS: list[str] = field(
        default_factory=lambda: ["ind+eng", "eng", "ind"]
    )

    # External tools detection
    TESSERACT_CMD: str | None = None
    POPPLER_PATH: str | None = None

    # Performance
    MAX_CONCURRENT_JOBS: int = 1  # Conservative CPU limit (recommended for local CPU)
    CLEANUP_TEMP_FILES: bool = True
    LOG_LEVEL: str = "INFO"

    def __post_init__(self):
        self.INPUT_DIR = self.BASE_DIR / "input"
        self.OUTPUT_DIR = self.BASE_DIR / "output"
        self.TEMP_DIR = self.BASE_DIR / "temp"
        self.LOGS_DIR = self.BASE_DIR / "logs"

        # Ensure directory structures exist
        for directory in [self.INPUT_DIR, self.OUTPUT_DIR, self.TEMP_DIR, self.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        self._detect_external_tools()

    def _detect_external_tools(self):
        """Locate Tesseract and Poppler on the system or via environment variables."""
        # Tesseract detection
        env_tesseract = os.environ.get("TESSERACT_CMD")
        if env_tesseract and Path(env_tesseract).exists():
            self.TESSERACT_CMD = env_tesseract
        else:
            system_tesseract = shutil.which("tesseract")
            if system_tesseract:
                self.TESSERACT_CMD = system_tesseract
            elif Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe").exists():
                self.TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        # Poppler detection
        env_poppler = os.environ.get("POPPLER_PATH")
        if env_poppler and Path(env_poppler).exists():
            self.POPPLER_PATH = env_poppler
        else:
            system_pdftoppm = shutil.which("pdftoppm")
            if system_pdftoppm:
                self.POPPLER_PATH = str(Path(system_pdftoppm).parent)
            elif Path(r"C:\Tools\poppler-26.09.0\Library\bin").exists():
                self.POPPLER_PATH = r"C:\Tools\poppler-26.09.0\Library\bin"


settings = AppSettings()
