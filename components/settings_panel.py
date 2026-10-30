"""Settings panel component for document conversion options."""

from typing import Any

import streamlit as st

from config.settings import settings


def render_conversion_options() -> dict[str, Any]:
    """Render conversion configuration controls in the conversion page.

    Returns:
        Dictionary containing selected options.
    """
    with st.expander("⚙️ Conversion & OCR Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            engine_choice = st.selectbox(
                "Conversion Engine",
                options=["auto", "docling", "markitdown"],
                index=0,
                format_func=lambda x: {
                    "auto": "Automatic (Smart Selection & Fallback)",
                    "docling": "Docling (High Accuracy, Complex PDF, Tables)",
                    "markitdown": "Microsoft MarkItDown (Fast, General Documents)",
                }.get(x, x),
                help="Pilih engine konversi. Mode Automatic memilih engine terbaik sesuai jenis file dengan fallback.",
            )

            markdown_style = st.selectbox(
                "Markdown Output Style",
                options=settings.MARKDOWN_STYLES,
                index=0,
                format_func=lambda x: {
                    "standard": "Standard Markdown (Clean content)",
                    "with_metadata": "With Metadata (YAML Frontmatter)",
                    "with_images": "With Image References",
                    "rag": "RAG Optimized (Delimited Sections for AI Search)",
                }.get(x, x),
                help="Format dan struktur akhir teks Markdown.",
            )

        with col2:
            ocr_enabled = st.checkbox(
                "Aktifkan OCR (Optical Character Recognition)",
                value=settings.OCR_ENABLED,
                help="Gunakan OCR untuk mengekstrak teks dari gambar atau PDF hasil scan.",
            )

            ocr_lang = st.selectbox(
                "Bahasa OCR",
                options=settings.SUPPORTED_OCR_LANGS,
                index=0,
                disabled=not ocr_enabled,
                format_func=lambda x: {
                    "ind+eng": "Indonesia + Inggris (Recommended)",
                    "eng": "English (Inggris)",
                    "ind": "Bahasa Indonesia",
                }.get(x, x),
            )

            extract_images = st.checkbox(
                "Ekstrak Gambar & Diagram",
                value=True,
                help="Simpan gambar dokumen ke folder terpisah dan hubungkan dengan relative path Markdown.",
            )

    return {
        "engine": engine_choice,
        "ocr_enabled": ocr_enabled,
        "ocr_lang": ocr_lang,
        "markdown_style": markdown_style,
        "extract_images": extract_images,
    }
