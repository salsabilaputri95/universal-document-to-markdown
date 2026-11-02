"""UI component for Markdown -> Word / PDF / PPTX conversion."""

import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from config.settings import settings
from core.markdown_exporter import (
    FORMAT_LABELS,
    FORMAT_MIME,
    MarkdownExporter,
    MarkdownExportResult,
)
from utils.file_utils import sanitize_filename


def render_md_to_doc_page() -> None:
    """Render the Markdown to Word / PDF / PPTX conversion interface."""
    st.markdown("## 📝 Markdown to Document")
    st.caption(
        "Konversi file atau teks Markdown (.md) menjadi dokumen Word (.docx), PDF (.pdf), "
        "dan PowerPoint (.pptx) dengan mempertahankan heading, numbering, bullets, tabel, gambar, dan formatting."
    )

    # 1. Input Mode Tabs
    input_tab1, input_tab2 = st.tabs(["📂 Unggah File Markdown", "✍️ Tulis / Tempel Teks Markdown"])

    md_text = ""
    source_name = "dokumen.md"
    upload_base_dir: Path | None = None
    extra_images: dict[str, Path] = {}

    with input_tab1:
        uploaded_md = st.file_uploader(
            "Pilih file Markdown (.md, .markdown)",
            type=["md", "markdown"],
            key="uploader_md_file",
            help="Unggah dokumen Markdown yang ingin dikonversi.",
        )
        if uploaded_md is not None:
            source_name = uploaded_md.name
            try:
                raw_bytes = uploaded_md.getvalue()
                md_text = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                md_text = raw_bytes.decode("utf-8", errors="replace")
                st.warning("File memuat karakter non-UTF8 yang disesuaikan secara otomatis.")

    with input_tab2:
        default_sample = (
            "# Judul Dokumen\n\n"
            "Paragraf pengantar dengan **teks tebal**, *miring*, ~~coret~~, dan `kode inline`.\n\n"
            "## Daftar Bernomor\n\n"
            "1. Langkah pertama\n"
            "2. Langkah kedua\n"
            "   1. Sub-langkah 2a\n"
            "   2. Sub-langkah 2b\n"
            "3. Langkah ketiga\n\n"
            "## Poin Berbutir\n\n"
            "- Fitur utama sistem\n"
            "- Dukungan multi-format\n"
            "  - Word (.docx)\n"
            "  - PDF (.pdf)\n"
            "  - PowerPoint (.pptx)\n\n"
            "## Data Tabel\n\n"
            "| Item | Kategori | Jumlah | Status |\n"
            "|:-----|:---------|-------:|:------:|\n"
            "| Server Alpha | Infrastruktur | 2 | Aktif |\n"
            "| Database Beta | Penyimpanan | 4 | Siap |\n\n"
            "```python\n"
            "# Contoh blok kode\n"
            "def proses():\n"
            "    return True\n"
            "```\n"
        )
        pasted_text = st.text_area(
            "Tulis atau tempel teks Markdown:",
            value=default_sample if not uploaded_md else "",
            height=260,
            key="textarea_md_input",
            help="Ketik langsung sintaks Markdown di sini.",
        )
        if not uploaded_md and pasted_text.strip():
            md_text = pasted_text
            source_name = "dokumen_markdown.md"

    # 2. Optional Asset Images Uploader
    with st.expander("🖼️ Gambar Aset Pendukung (Opsional)", expanded=False):
        st.caption(
            "Jika file Markdown merujuk ke gambar lokal (misalnya `![diagram](doc_assets/image_001.png)` "
            "atau `![foto](gambar.png)`), unggah file gambarnya di sini agar otomatis disertakan."
        )
        uploaded_images = st.file_uploader(
            "Pilih gambar pendukung",
            type=["png", "jpg", "jpeg", "gif", "bmp"],
            accept_multiple_files=True,
            key="uploader_extra_images",
        )
        if uploaded_images:
            temp_img_dir = Path(tempfile.mkdtemp(prefix="omnimark_images_"))
            for img in uploaded_images:
                safe_img_name = sanitize_filename(img.name)
                img_path = temp_img_dir / safe_img_name
                img_path.write_bytes(img.getvalue())
                extra_images[safe_img_name.lower()] = img_path
                extra_images[img.name.lower()] = img_path
            st.success(f"{len(uploaded_images)} gambar terunggah dan siap ditautkan.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Output Format Options & Settings
    st.markdown("### ⚙️ Pilihan Format Output")
    col_fmt1, col_fmt2, col_fmt3 = st.columns(3)
    with col_fmt1:
        want_docx = st.checkbox("📄 Microsoft Word (.docx)", value=True)
    with col_fmt2:
        want_pdf = st.checkbox("📕 PDF Document (.pdf)", value=True)
    with col_fmt3:
        want_pptx = st.checkbox("📊 PowerPoint (.pptx)", value=True)

    target_formats = []
    if want_docx:
        target_formats.append("docx")
    if want_pdf:
        target_formats.append("pdf")
    if want_pptx:
        target_formats.append("pptx")

    with st.expander("🛠️ Pengaturan Format Lanjutan", expanded=False):
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            pdf_page_size = st.selectbox(
                "Ukuran Halaman PDF",
                options=settings.PDF_PAGE_SIZES,
                index=0,
                help="Ukuran kertas dokumen PDF yang dihasilkan.",
            )
        with col_opt2:
            slide_split = st.selectbox(
                "Pemisahan Slide PowerPoint (PPTX)",
                options=[2, 1],
                index=0,
                format_func=lambda x: "Heading 2 (##) [Disarankan]" if x == 2 else "Heading 1 (#) Saja",
                help="Menentukan heading mana yang memicu pembuatan slide baru di PowerPoint.",
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Conversion Trigger Button
    if not md_text.strip():
        st.info("💡 Unggah file atau tulis teks Markdown di atas untuk memulai konversi.")
        return

    if not target_formats:
        st.warning("Pilih minimal satu format output (Word, PDF, atau PowerPoint).")
        return

    btn_label = f"⚡ Konversi ke {len(target_formats)} Format ({', '.join(f.upper() for f in target_formats)})"
    if st.button(btn_label, type="primary", use_container_width=True, key="btn_convert_md_to_doc"):
        with st.spinner("Sedang mengonversi dokumen..."):
            exporter = MarkdownExporter(
                page_size=pdf_page_size,
                slide_split_level=slide_split,
            )

            result: MarkdownExportResult = exporter.export_text(
                markdown_text=md_text,
                base_name=source_name,
                formats=target_formats,
                output_dir=settings.MD_EXPORT_DIR,
                base_dirs=[upload_base_dir] if upload_base_dir else None,
                extra_images=extra_images,
            )
            st.session_state.last_md_export_result = result

    # 5. Display Results
    last_res: MarkdownExportResult | None = st.session_state.get("last_md_export_result")
    if last_res:
        st.markdown("---")
        st.markdown(f"### 📋 Hasil Konversi dari `{last_res.source_name}`")

        if last_res.error_message:
            st.error(f"Gagal memproses dokumen: {last_res.error_message}")
            return

        if last_res.parse_warnings:
            for w in last_res.parse_warnings:
                st.warning(f"ℹ️ {w}")

        # Render result per format
        successful_files = []
        for file_res in last_res.files:
            fmt_upper = file_res.format.upper()
            fmt_label = FORMAT_LABELS.get(file_res.format, fmt_upper)

            if file_res.success and file_res.output_path and file_res.output_path.is_file():
                successful_files.append(file_res)
                border_color = "#10B981"
                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {border_color}; background-color: #FFFFFF;
                                border: 1px solid #E2E8F0; border-left-color: {border_color};
                                border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                            <span style="font-weight: 600; font-size: 1.05rem; color: #0F172A;">
                                📄 {fmt_label}
                            </span>
                            <span style="font-size: 0.85rem; font-weight: 600; padding: 0.2rem 0.6rem;
                                         border-radius: 9999px; background-color: #D1FAE5; color: #065F46;">
                                ✅ Siap Diunduh
                            </span>
                        </div>
                        <div style="display: flex; gap: 1.5rem; font-size: 0.85rem; color: #64748B;">
                            <span><b>Ukuran:</b> {file_res.file_size_formatted}</span>
                            <span><b>Durasi:</b> {file_res.duration_seconds}s</span>
                            <span><b>Berkas:</b> <code>{file_res.output_path.name}</code></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if file_res.warnings:
                    for w in file_res.warnings:
                        st.info(f"⚠️ {w}")

                with open(file_res.output_path, "rb") as out_f:
                    data_bytes = out_f.read()

                st.download_button(
                    label=f"📥 Download {file_res.output_path.name} ({file_res.file_size_formatted})",
                    data=data_bytes,
                    file_name=file_res.output_path.name,
                    mime=FORMAT_MIME.get(file_res.format, "application/octet-stream"),
                    key=f"dl_md_export_{file_res.format}_{file_res.output_path.name}",
                    type="primary",
                )
                st.markdown("<br>", unsafe_allow_html=True)

            else:
                st.markdown(
                    f"""
                    <div style="border-left: 4px solid #EF4444; background-color: #FFFFFF;
                                border: 1px solid #E2E8F0; border-left-color: #EF4444;
                                border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                            <span style="font-weight: 600; font-size: 1.05rem; color: #0F172A;">
                                📄 {fmt_label}
                            </span>
                            <span style="font-size: 0.85rem; font-weight: 600; padding: 0.2rem 0.6rem;
                                         border-radius: 9999px; background-color: #FEE2E2; color: #991B1B;">
                                ❌ Gagal
                            </span>
                        </div>
                        <div style="font-size: 0.85rem; color: #DC2626;">
                            <b>Error:</b> {file_res.error_message or 'Terjadi kesalahan saat rendering.'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Batch ZIP download if multiple files succeeded
        if len(successful_files) > 1:
            zip_stem = Path(sanitize_filename(last_res.source_name)).stem
            zip_filename = f"{zip_stem}_documents.zip"
            zip_target = settings.MD_EXPORT_DIR / zip_filename

            with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zf:
                for sf in successful_files:
                    if sf.output_path and sf.output_path.is_file():
                        zf.write(sf.output_path, arcname=sf.output_path.name)

            with open(zip_target, "rb") as zf_read:
                zip_bytes = zf_read.read()

            st.download_button(
                label=f"📦 Download Semua Dokumen Sekaligus ({len(successful_files)} Berkas) sebagai ZIP",
                data=zip_bytes,
                file_name=zip_filename,
                mime="application/zip",
                key="dl_batch_md_export_zip",
            )
