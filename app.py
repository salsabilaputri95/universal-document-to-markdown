"""Universal Document to Markdown — Main Streamlit Application."""

import streamlit as st

from components.history import render_history_page
from components.preview import render_preview_section
from components.result_card import render_result_card
from components.settings_panel import render_conversion_options
from components.sidebar import render_sidebar
from components.uploader import render_uploader
from config.settings import settings
from core.converter import ConversionManager, ConversionResult
from core.export_manager import ExportManager
from utils.file_utils import format_file_size
from utils.logger import logger

# Page configuration
st.set_page_config(
    page_title="OmniMark — Universal Document to Markdown",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "conversion_history" not in st.session_state:
    st.session_state.conversion_history = []
if "last_batch_results" not in st.session_state:
    st.session_state.last_batch_results = []
if "active_page" not in st.session_state:
    st.session_state.active_page = "convert"


def render_dashboard_page():
    """Render application dashboard with real-time conversion statistics."""
    st.markdown("## 📊 Dashboard")
    st.caption("Ringkasan performa dan metrik pemrosesan dokumen lokal.")

    history: list[ConversionResult] = st.session_state.conversion_history

    total_docs = len(history)
    successful_docs = sum(1 for r in history if r.success)
    failed_docs = total_docs - successful_docs
    total_bytes = sum(r.file_size_bytes for r in history)

    # Top metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Dokumen Diproses", total_docs)
    with col2:
        st.metric(
            "Berhasil",
            successful_docs,
            delta=f"{successful_docs / total_docs * 100:.0f}%" if total_docs > 0 else "0%",
        )
    with col3:
        st.metric("Gagal", failed_docs)
    with col4:
        st.metric("Total Ukuran Data", format_file_size(total_bytes))

    st.markdown("---")

    # Format Breakdown
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📂 Distribusi Format File")
        if history:
            ext_counts = {}
            for r in history:
                ext = r.extension.upper()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            st.bar_chart(ext_counts)
        else:
            st.info("Belum ada data riwayat untuk menampilkan grafik format file.")

    with col_right:
        st.markdown("#### ⚡ Distribusi Engine Konversi")
        if history:
            engine_counts = {}
            for r in history:
                eng = r.used_engine
                engine_counts[eng] = engine_counts.get(eng, 0) + 1
            st.bar_chart(engine_counts)
        else:
            st.info("Belum ada data riwayat untuk menampilkan grafik engine.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Mulai Konversi Dokumen Baru", type="primary"):
        st.session_state.active_page = "convert"
        st.rerun()


def render_convert_page():
    """Render the main document conversion workflow page."""
    st.markdown("## 🔄 Convert Documents to Markdown")
    st.caption(
        "Konversi dokumen (.pdf, .docx, .xlsx, .pptx, .csv) ke Markdown "
        "dengan struktur rapi dan aman secara lokal."
    )

    # 1. Options panel
    options = render_conversion_options()

    # 2. File uploader & validation
    valid_paths = render_uploader()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Conversion trigger button
    if valid_paths:
        if st.button(f"⚡ Konversi {len(valid_paths)} Dokumen Sekarang", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            manager = ConversionManager(
                ocr_enabled=options["ocr_enabled"],
                ocr_lang=options["ocr_lang"],
                markdown_style=options["markdown_style"],
                extract_images=options["extract_images"],
            )

            batch_results: list[ConversionResult] = []
            total_files = len(valid_paths)

            for idx, file_p in enumerate(valid_paths):
                file_name = file_p.name
                status_text.markdown(f"⏳ Sedang memproses ({idx + 1}/{total_files}): **{file_name}**...")
                progress_bar.progress(idx / total_files)

                # Process single file with isolated error handling
                res = manager.convert_file(
                    file_path=file_p,
                    engine_choice=options["engine"],
                )
                batch_results.append(res)
                st.session_state.conversion_history.append(res)

            progress_bar.progress(1.0)
            status_text.success("🎉 Seluruh dokumen selesai diproses!")
            st.session_state.last_batch_results = batch_results

    # 4. Display Results if any
    current_results = st.session_state.last_batch_results
    if current_results:
        st.markdown("---")
        st.markdown("### 📋 Hasil Konversi Dokumen")

        # Result Cards
        for res in current_results:
            render_result_card(res)

        # Batch Export Action (ZIP)
        successful_items = [r for r in current_results if r.success]
        if successful_items:
            try:
                zip_path = ExportManager.create_batch_zip(
                    results=successful_items,
                    zip_filename="markdown-export.zip",
                )
                with open(zip_path, "rb") as zf:
                    zip_bytes = zf.read()

                st.download_button(
                    label=f"📦 Download Semua Hasil ({len(successful_items)} Dokumen & Gambar) sebagai ZIP",
                    data=zip_bytes,
                    file_name="markdown-export.zip",
                    mime="application/zip",
                    type="primary",
                    key="dl_batch_zip",
                )
            except Exception as zip_err:
                logger.error(f"Failed to prepare batch ZIP: {zip_err}")
                st.error(f"Gagal menyiapkan arsip ZIP: {zip_err}")

        # 5. Preview Section
        render_preview_section(current_results)


def render_settings_page():
    """Render application settings inspection and configuration."""
    st.markdown("## ⚙️ Application Settings & Diagnostics")
    st.caption("Pemeriksaan konfigurasi sistem dan utilitas eksternal.")

    st.markdown("#### 📁 Lokasi Direktori Kerja")
    st.code(
        f"Base Dir:   {settings.BASE_DIR}\n"
        f"Input Dir:  {settings.INPUT_DIR}\n"
        f"Output Dir: {settings.OUTPUT_DIR}\n"
        f"Temp Dir:   {settings.TEMP_DIR}\n"
        f"Logs Dir:   {settings.LOGS_DIR}",
        language="text",
    )

    st.markdown("#### 🔍 Utilitas Eksternal (Windows)")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Tesseract OCR**")
        if settings.TESSERACT_CMD:
            st.success(f"Ditemukan di: `{settings.TESSERACT_CMD}`")
        else:
            st.warning("Executable Tesseract tidak ditemukan di PATH.")

    with col2:
        st.markdown("**Poppler (PDF Utilities)**")
        if settings.POPPLER_PATH:
            st.success(f"Ditemukan di: `{settings.POPPLER_PATH}`")
        else:
            st.warning("Executable Poppler tidak ditemukan di PATH.")

    st.markdown("#### 🛡️ Kebijakan Pemrosesan & Resource")
    st.markdown(
        """
        - **CPU Processing**: Aktif secara bawaan, aman tanpa GPU NVIDIA.
        - **Batas Ukuran Upload**: Maksimal 100 MB per file.
        - **Isolasi Memori**: Single-file concurrency terkendali untuk mencegah kehabisan RAM.
        - **Privasi**: Tidak ada data yang dikirim ke server cloud atau API pihak ketiga.
        """
    )


def render_about_page():
    """Render technical information and architecture details."""
    st.markdown("## ℹ️ About OmniMark")
    st.markdown(
        """
        **OmniMark** adalah aplikasi desktop-web lokal modern untuk mengonversi berbagai format dokumen
        menjadi Markdown (`.md`) dengan mempertahankan hierarki heading, tabel data, daftar berbutir,
        serta ekstraksi gambar visual secara aman (*local-first*).

        ### 🏗️ Arsitektur & Teknologi
        - **Nama Produk**: OmniMark
        - **Framework UI**: Streamlit 1.66+
        - **Primary Engine**: IBM Docling (Layout analysis, complex tables, OCR)
        - **Alternative Engine**: Microsoft MarkItDown (Universal document conversion)
        - **Excel Engine**: OpenPyXL & Pandas (Multi-sheet, merged cells, cached formulas)
        - **OCR Utilities**: Tesseract OCR & Poppler
        - **Standard**: Markdown GFM (GitHub Flavored Markdown)

        ### 🔒 Komitmen Local-First
        - Semua komputasi berlangsung di CPU komputer lokal pengguna.
        - Dokumen tidak pernah dikirimkan ke cloud atau API eksternal manapun.
        - Tanpa ketergantungan model AI online atau Ollama.
        """
    )


def main():
    selected_page = render_sidebar()

    if selected_page == "convert":
        render_convert_page()
    elif selected_page == "dashboard":
        render_dashboard_page()
    elif selected_page == "history":
        render_history_page()
    elif selected_page == "settings":
        render_settings_page()
    elif selected_page == "about":
        render_about_page()


if __name__ == "__main__":
    main()
