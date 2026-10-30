"""File validation module for Universal Document to Markdown.

Validates extensions, file sizes, MIME types / magic bytes, encryption, and empty files.
"""

import zipfile
from dataclasses import dataclass
from pathlib import Path

from config.settings import settings
from utils.file_utils import sanitize_filename
from utils.logger import logger


@dataclass
class ValidationResult:
    """Holds the result of document validation."""

    is_valid: bool
    file_path: Path
    filename: str
    extension: str
    file_size_bytes: int
    mime_type: str = "application/octet-stream"
    error_message: str | None = None
    is_encrypted: bool = False


class FileValidator:
    """Validator for input documents prior to conversion."""

    # Magic byte signatures
    MAGIC_SIGNATURES: dict[str, list[bytes]] = {
        ".pdf": [b"%PDF-"],
        ".docx": [b"PK\x03\x04"],
        ".xlsx": [b"PK\x03\x04"],
        ".pptx": [b"PK\x03\x04"],
    }

    OLE_ENCRYPTION_HEADER = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    @classmethod
    def validate_file(cls, file_path: Path | str) -> ValidationResult:
        """Thoroughly validate a document file on disk."""
        path = Path(file_path)

        # 1. Existence check
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                file_path=path,
                filename=path.name,
                extension=path.suffix.lower(),
                file_size_bytes=0,
                error_message=f"File not found: {path.name}",
            )

        filename = sanitize_filename(path.name)
        extension = path.suffix.lower()
        file_size = path.stat().st_size

        # 2. Extension validation
        if extension not in settings.SUPPORTED_EXTENSIONS:
            allowed = ", ".join(settings.SUPPORTED_EXTENSIONS)
            return ValidationResult(
                is_valid=False,
                file_path=path,
                filename=filename,
                extension=extension,
                file_size_bytes=file_size,
                error_message=(
                    f"Format file '{extension}' tidak didukung. "
                    f"Format yang didukung: {allowed}"
                ),
            )

        # 3. Empty file check
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                file_path=path,
                filename=filename,
                extension=extension,
                file_size_bytes=0,
                error_message=f"File '{filename}' kosong (0 byte).",
            )

        # 4. File size limit
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return ValidationResult(
                is_valid=False,
                file_path=path,
                filename=filename,
                extension=extension,
                file_size_bytes=file_size,
                error_message=(
                    f"Ukuran file '{filename}' melebihi batas maksimum "
                    f"({settings.MAX_FILE_SIZE_MB} MB)."
                ),
            )

        # 5. Header / Magic Bytes check
        is_encrypted = False
        detected_mime = "application/octet-stream"

        try:
            with open(path, "rb") as f:
                header = f.read(512)

            if extension in cls.MAGIC_SIGNATURES:
                expected_magics = cls.MAGIC_SIGNATURES[extension]
                matches_magic = any(header.startswith(m) for m in expected_magics)

                # Check for password-protected / encrypted Office file (often stored as OLE compound)
                if not matches_magic and header.startswith(cls.OLE_ENCRYPTION_HEADER):
                    is_encrypted = True
                    return ValidationResult(
                        is_valid=False,
                        file_path=path,
                        filename=filename,
                        extension=extension,
                        file_size_bytes=file_size,
                        is_encrypted=True,
                        error_message=(
                            f"File '{filename}' terenkripsi atau dilindungi kata sandi. "
                            "Mohon buka proteksi file sebelum mengonversi."
                        ),
                    )

                if not matches_magic:
                    return ValidationResult(
                        is_valid=False,
                        file_path=path,
                        filename=filename,
                        extension=extension,
                        file_size_bytes=file_size,
                        error_message=(
                            f"Struktur isi file '{filename}' tidak sesuai dengan ekstensi '{extension}' "
                            "(file rusak atau salah ekstensi)."
                        ),
                    )

            # Specific check for encrypted PDF
            if extension == ".pdf":
                detected_mime = "application/pdf"
                try:
                    import pypdfium2

                    # Opening without password will raise PdfiumError with password code if encrypted
                    doc = pypdfium2.PdfDocument(path)
                    doc.close()
                except Exception as pdf_err:
                    err_msg = str(pdf_err).lower()
                    if "password" in err_msg:
                        return ValidationResult(
                            is_valid=False,
                            file_path=path,
                            filename=filename,
                            extension=extension,
                            file_size_bytes=file_size,
                            is_encrypted=True,
                            error_message=(
                                f"Dokumen PDF '{filename}' dilindungi kata sandi. "
                                "Mohon hapus kata sandi terlebih dahulu."
                            ),
                        )
                    logger.warning(f"PDF pre-check warning for {filename}: {pdf_err}")

            # Specific check for Office Open XML files (DOCX, XLSX, PPTX)
            elif extension in [".docx", ".xlsx", ".pptx"]:
                try:
                    with zipfile.ZipFile(path, "r") as zf:
                        # Test if any member is password protected
                        for zinfo in zf.infolist():
                            if zinfo.flag_bits & 0x1:
                                return ValidationResult(
                                    is_valid=False,
                                    file_path=path,
                                    filename=filename,
                                    extension=extension,
                                    file_size_bytes=file_size,
                                    is_encrypted=True,
                                    error_message=(
                                        f"File Office '{filename}' dilindungi kata sandi. "
                                        "Mohon hapus proteksi file terlebih dahulu."
                                    ),
                                )
                except zipfile.BadZipFile:
                    return ValidationResult(
                        is_valid=False,
                        file_path=path,
                        filename=filename,
                        extension=extension,
                        file_size_bytes=file_size,
                        error_message=f"File '{filename}' rusak (Bad ZIP/Office structure).",
                    )

            elif extension == ".csv":
                detected_mime = "text/csv"
                # Check readable text encoding
                try:
                    with open(path, encoding="utf-8", errors="replace") as cf:
                        sample = cf.read(1024)
                        if not sample.strip():
                            return ValidationResult(
                                is_valid=False,
                                file_path=path,
                                filename=filename,
                                extension=extension,
                                file_size_bytes=file_size,
                                error_message=f"File CSV '{filename}' kosong atau tidak berisi teks valid.",
                            )
                except Exception as csv_err:
                    return ValidationResult(
                        is_valid=False,
                        file_path=path,
                        filename=filename,
                        extension=extension,
                        file_size_bytes=file_size,
                        error_message=f"Tidak dapat membaca file CSV '{filename}': {csv_err}",
                    )

        except Exception as err:
            logger.error(f"Error validating file {filename}: {err}")
            return ValidationResult(
                is_valid=False,
                file_path=path,
                filename=filename,
                extension=extension,
                file_size_bytes=file_size,
                error_message=f"Gagal memvalidasi file: {err}",
            )

        return ValidationResult(
            is_valid=True,
            file_path=path,
            filename=filename,
            extension=extension,
            file_size_bytes=file_size,
            mime_type=detected_mime,
            is_encrypted=is_encrypted,
        )

