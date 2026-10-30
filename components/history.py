"""Conversion history component tracking all session conversions."""

import streamlit as st

from core.converter import ConversionResult
from core.export_manager import ExportManager
from utils.file_utils import format_file_size


def render_history_page() -> None:
    """Render the conversion history page."""
    st.markdown("## 📜 Conversion History")
    st.caption("Riwayat konversi dokumen selama sesi aplikasi berjalan.")

    history: list[ConversionResult] = st.session_state.get("conversion_history", [])

    if not history:
        st.info("Belum ada dokumen yang dikonversi pada sesi ini. Buka menu 'Convert Documents' untuk memulai.")
        return

    # Summary Metrics
    total = len(history)
    successful = sum(1 for r in history if r.success)
    failed = total - successful
    total_bytes = sum(r.file_size_bytes for r in history)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Dokumen", total)
    with col2:
        st.metric("Berhasil", successful, delta=f"{successful / total * 100:.0f}%" if total > 0 else None)
    with col3:
        st.metric("Gagal", failed)
    with col4:
        st.metric("Total Ukuran", format_file_size(total_bytes))

    st.markdown("---")

    # Filter controls
    col_filter, col_action = st.columns([3, 1])
    with col_filter:
        status_filter = st.selectbox(
            "Filter berdasarkan status:",
            options=["Semua", "Berhasil", "Fallback Digunakan", "Gagal"],
            index=0,
        )

    with col_action:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Hapus Riwayat", use_container_width=True):
            st.session_state.conversion_history = []
            st.rerun()

    filtered_history = history
    if status_filter == "Berhasil":
        filtered_history = [r for r in history if r.success and not r.fallback_used]
    elif status_filter == "Fallback Digunakan":
        filtered_history = [r for r in history if r.success and r.fallback_used]
    elif status_filter == "Gagal":
        filtered_history = [r for r in history if not r.success]

    # Render History Table
    table_data = []
    for r in reversed(filtered_history):
        status_badge = "✅ Sukses" if r.success else "❌ Gagal"
        if r.fallback_used:
            status_badge = "⚠️ Fallback"

        table_data.append({
            "Waktu": r.converted_at,
            "Nama File": r.filename,
            "Format": r.extension.upper(),
            "Ukuran": r.file_size_formatted,
            "Engine Digunakan": r.used_engine,
            "Durasi": f"{r.duration_seconds}s",
            "Kata": f"{r.stats.get('words', 0):,}" if r.success else "-",
            "Status": status_badge,
        })

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Download Metadata of History
    if history:
        meta_filename, meta_bytes = ExportManager.export_metadata_json(history)
        st.download_button(
            label="📥 Export Riwayat Lengkap (JSON)",
            data=meta_bytes,
            file_name=meta_filename,
            mime="application/json",
            key="dl_history_json",
        )
