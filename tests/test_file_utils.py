"""Unit tests for file utility functions."""

from utils.file_utils import (
    cleanup_directory,
    create_isolated_temp_dir,
    format_file_size,
    is_safe_path,
    sanitize_filename,
)


def test_sanitize_filename():
    # Reserved characters
    dirty = 'my:document<version>?*"1.pdf'
    cleaned = sanitize_filename(dirty)
    assert ":" not in cleaned
    assert "<" not in cleaned
    assert "?" not in cleaned
    assert "*" not in cleaned
    assert cleaned.endswith(".pdf")

    # Windows reserved names
    assert sanitize_filename("CON.docx").startswith("document_")
    assert sanitize_filename("nul.pdf").startswith("document_")
    assert sanitize_filename("com1.xlsx").startswith("document_")

    # Path traversal characters
    traversal = "../../secret_file.pdf"
    clean_trav = sanitize_filename(traversal)
    assert "/" not in clean_trav
    assert "\\" not in clean_trav
    assert "secret_file.pdf" in clean_trav


def test_format_file_size():
    assert format_file_size(0) == "0 B"
    assert format_file_size(500) == "500 B"
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1048576) == "1.00 MB"
    assert format_file_size(1073741824) == "1.00 GB"


def test_is_safe_path(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    child_file = base_dir / "child.txt"
    outside_file = tmp_path / "outside.txt"

    assert is_safe_path(base_dir, child_file) is True
    assert is_safe_path(base_dir, base_dir) is True
    assert is_safe_path(base_dir, outside_file) is False


def test_isolated_temp_dir():
    temp_dir = create_isolated_temp_dir("test_job_")
    assert temp_dir.exists()
    assert "test_job_" in temp_dir.name

    dummy_file = temp_dir / "dummy.txt"
    dummy_file.write_text("sample")
    assert dummy_file.exists()

    assert cleanup_directory(temp_dir) is True
    assert not temp_dir.exists()

