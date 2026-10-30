"""Markdown preview component with tabs for Rendered and Source views."""

import streamlit as st

from core.converter import ConversionResult
from core.export_manager import ExportManager


def render_preview_section(results: list[ConversionResult]) -> None:
    """Render preview and individual download section for successful conversions."""
    successful_results = [r for r in results if r.success and r.markdown_content]

    if not successful_results:
        return

    st.markdown("### 👁️ Preview & Download Hasil")

    # Document Selector if multiple documents
    doc_options = {r.filename: r for r in successful_results}
    selected_name = st.selectbox(
        "Pilih dokumen untuk di-preview:",
        options=list(doc_options.keys()),
        index=0,
    )
    selected_res = doc_options[selected_name]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Jumlah Kata", f"{selected_res.stats.get('words', 0):,}")
    with col2:
        st.metric("Jumlah Karakter", f"{selected_res.stats.get('characters', 0):,}")
    with col3:
        st.metric("Jumlah Baris", f"{selected_res.stats.get('lines', 0):,}")
    with col4:
        st.metric("Durasi Proses", f"{selected_res.duration_seconds}s")

    # Action bar (Download single .md)
    md_filename, md_bytes = ExportManager.export_single_markdown(selected_res)
    st.download_button(
        label=f"📥 Download '{md_filename}'",
        data=md_bytes,
        file_name=md_filename,
        mime="text/markdown",
        key=f"dl_single_{selected_res.filename}",
        type="primary",
    )

    # Tabs: Rendered vs Source
    tab_rendered, tab_source, tab_images = st.tabs(["📄 Rendered Markdown", "💻 Source Code", "🖼️ Extracted Images"])

    with tab_rendered:
        st.markdown(selected_res.markdown_content, unsafe_allow_html=True)

    with tab_source:
        st.text_area(
            "Markdown Source",
            value=selected_res.markdown_content,
            height=400,
            help="Anda dapat menyalin teks Markdown langsung dari sini.",
        )

    with tab_images:
        if selected_res.extracted_images and selected_res.asset_dir:
            st.markdown(f"**Ditemukan {len(selected_res.extracted_images)} gambar:**")
            cols = st.columns(min(len(selected_res.extracted_images), 3))
            for idx, img_info in enumerate(selected_res.extracted_images):
                col = cols[idx % 3]
                img_path = selected_res.asset_dir / img_info["filename"]
                if img_path.is_file():
                    with col:
                        caption_text = img_info.get("caption") or img_info["filename"]
                        st.image(str(img_path), caption=caption_text, use_container_width=True)
        else:
            st.info("Dokumen ini tidak memiliki gambar atau ekstraksi gambar tidak menghasilkan file visual.")
