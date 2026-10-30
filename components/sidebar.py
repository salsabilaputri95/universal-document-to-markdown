"""Sidebar component for navigation and system status."""

import streamlit as st

from config.settings import settings


def render_sidebar() -> str:
    """Render the application sidebar navigation and status summary.

    Returns:
        The selected page identifier.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom: 1rem; border-bottom: 1px solid #E2E8F0; margin-bottom: 1.5rem;">
                <h2 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: #0F172A; letter-spacing: -0.02em;">
                    ⚡ OmniMark
                </h2>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem; color: #64748B;">
                    Universal Document to Markdown
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation options
        pages = {
            "convert": ("🔄", "Convert Documents"),
            "dashboard": ("📊", "Dashboard"),
            "history": ("📜", "Conversion History"),
            "settings": ("⚙️", "Settings"),
            "about": ("ℹ️", "About"),
        }

        # Ensure active_page in session state
        if "active_page" not in st.session_state:
            st.session_state.active_page = "convert"

        for page_id, (icon, label) in pages.items():
            is_active = st.session_state.active_page == page_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_id}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.active_page = page_id
                st.rerun()

        st.markdown(
            "<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E2E8F0;'/>",
            unsafe_allow_html=True,
        )

        # System Status Widget
        st.markdown("#### System Status")
        st.caption("💻 Local CPU Processing")

        tesseract_status = "✅ Ready" if settings.TESSERACT_CMD else "⚠️ Not Found"
        poppler_status = "✅ Ready" if settings.POPPLER_PATH else "⚠️ Not Found"

        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0;
                        border-radius: 6px; padding: 0.75rem; font-size: 0.8rem; line-height: 1.5;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #64748B;">Python:</span>
                    <span style="font-weight: 600; color: #0F172A;">3.13.5</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #64748B;">OCR (Tesseract):</span>
                    <span style="font-weight: 600;">{tesseract_status}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #64748B;">PDF (Poppler):</span>
                    <span style="font-weight: 600;">{poppler_status}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="margin-top: 2rem; font-size: 0.75rem; color: #94A3B8; text-align: center;">
                🔒 100% Offline & Private<br>No cloud • No external API
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.active_page
