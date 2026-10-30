"""Integration tests for Streamlit UI."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_ui_initial_render():
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception


def test_ui_navigate_pages():
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception

    # Simulate navigating to Dashboard
    at.session_state.active_page = "dashboard"
    at.run()
    assert not at.exception

    # Simulate navigating to History
    at.session_state.active_page = "history"
    at.run()
    assert not at.exception

    # Simulate navigating to Settings
    at.session_state.active_page = "settings"
    at.run()
    assert not at.exception

    # Simulate navigating to About
    at.session_state.active_page = "about"
    at.run()
    assert not at.exception
