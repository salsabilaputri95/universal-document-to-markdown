"""File upload and pre-conversion validation component."""

from pathlib import Path

import streamlit as st

from config.settings import settings
from core.file_validator import FileValidator, ValidationResult
from utils.file_utils import format_file_size, sanitize_filename
from utils.logger import logger


def render_uploader() -> list[Path]:
    """Render the file uploader and display pre-conversion validation summary.

    Returns:
        List of Path objects for validated, saved files ready for conversion.
    """
    st.markdown("### 📤 Upload Documents")

    supported_types = [ext.lstrip(".") for ext in settings.SUPPORTED_EXTENSIONS]

    supported_str = ", ".join(settings.SUPPORTED_EXTENSIONS)
    uploaded_files = st.file_uploader(
        "Pilih atau seret dokumen ke sini",
        type=supported_types,
        accept_multiple_files=True,
        help=f"Format yang didukung: {supported_str}. Maks {settings.MAX_FILE_SIZE_MB}MB per file.",
    )

    if not uploaded_files:
        st.info("💡 Unggah satu atau beberapa dokumen (.pdf, .docx, .xlsx, .pptx, .csv) untuk memulai konversi.")
        return []

    saved_paths: list[Path] = []
    validation_records: list[dict] = []

    settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        safe_name = sanitize_filename(uploaded_file.name)
        target_path = settings.INPUT_DIR / safe_name

        try:
            # Save uploaded bytes to local input dir
            target_path.write_bytes(uploaded_file.getbuffer())

            # Perform validation
            val_result: ValidationResult = FileValidator.validate_file(target_path)

            if val_result.is_valid:
                saved_paths.append(target_path)
                status_label = "✅ Siap Dikonversi"
                notes = f"Tipe: {val_result.mime_type}"
            else:
                status_label = "❌ Gagal Validasi"
                notes = val_result.error_message or "Format tidak valid"

            validation_records.append({
                "Nama File": uploaded_file.name,
                "Format": Path(uploaded_file.name).suffix.upper(),
                "Ukuran": format_file_size(uploaded_file.size),
                "Status": status_label,
                "Catatan": notes,
            })

        except Exception as err:
            logger.error(f"Error saving uploaded file {uploaded_file.name}: {err}")
            validation_records.append({
                "Nama File": uploaded_file.name,
                "Format": Path(uploaded_file.name).suffix.upper(),
                "Ukuran": format_file_size(uploaded_file.size),
                "Status": "❌ Error",
                "Catatan": str(err),
            })

    # Render summary table
    st.markdown(f"**Dokumen Terunggah ({len(uploaded_files)} file):**")
    st.dataframe(
        validation_records,
        use_container_width=True,
        hide_index=True,
    )

    valid_count = len(saved_paths)
    invalid_count = len(uploaded_files) - valid_count

    if invalid_count > 0:
        st.warning(f"Terdapat {invalid_count} file yang tidak memenuhi kriteria validasi dan tidak akan diproses.")

    return saved_paths
