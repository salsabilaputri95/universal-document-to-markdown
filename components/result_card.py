"""Result card component for displaying individual document conversion status."""

import streamlit as st

from core.converter import ConversionResult


def render_result_card(result: ConversionResult) -> None:
    """Render a card displaying the outcome of an individual file conversion."""
    if result.success:
        border_color = "#10B981"  # Emerald green
        status_badge = "✅ Success"
        if result.fallback_used:
            border_color = "#F59E0B"  # Amber
            status_badge = "⚠️ Fallback Used"

        st.markdown(
            f"""
            <div style="border-left: 4px solid {border_color}; background-color: #FFFFFF;
                        border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0;
                        border-bottom: 1px solid #E2E8F0; border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: #0F172A;">📄 {result.filename}</span>
                    <span style="font-size: 0.85rem; font-weight: 600; padding: 0.2rem 0.6rem;
                                 border-radius: 9999px; background-color: #F1F5F9;">{status_badge}</span>
                </div>
                <div style="display: flex; gap: 1.5rem; font-size: 0.85rem; color: #64748B;">
                    <span><b>Engine:</b> {result.used_engine}</span>
                    <span><b>Waktu:</b> {result.duration_seconds}s</span>
                    <span><b>Kata:</b> {result.stats.get('words', 0):,}</span>
                    <span><b>Karakter:</b> {result.stats.get('characters', 0):,}</span>
                    <span><b>Gambar:</b> {len(result.extracted_images)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if result.fallback_used and result.fallback_reason:
            st.warning(f"ℹ️ Engine dialihkan ke {result.used_engine}: {result.fallback_reason}")

        if result.warnings:
            for w in result.warnings:
                st.info(f"⚠️ {w}")

    else:
        st.markdown(
            f"""
            <div style="border-left: 4px solid #EF4444; background-color: #FFFFFF;
                        border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0;
                        border-bottom: 1px solid #E2E8F0; border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: #0F172A;">📄 {result.filename}</span>
                    <span style="font-size: 0.85rem; font-weight: 600; padding: 0.2rem 0.6rem;
                                 border-radius: 9999px; background-color: #FEE2E2; color: #991B1B;">❌ Gagal</span>
                </div>
                <div style="font-size: 0.85rem; color: #DC2626;">
                    <b>Alasan:</b> {result.error_message or 'Terjadi kesalahan tidak terduga'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
