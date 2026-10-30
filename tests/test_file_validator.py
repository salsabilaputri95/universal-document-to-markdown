"""Unit tests for document validator."""

from core.file_validator import FileValidator


def test_validate_nonexistent_file(tmp_path):
    result = FileValidator.validate_file(tmp_path / "does_not_exist.pdf")
    assert result.is_valid is False
    assert "File not found" in (result.error_message or "")


def test_validate_unsupported_extension(tmp_path):
    bad_file = tmp_path / "script.exe"
    bad_file.write_bytes(b"MZ\x90\x00")
    result = FileValidator.validate_file(bad_file)
    assert result.is_valid is False
    assert "tidak didukung" in (result.error_message or "")


def test_validate_empty_file(tmp_path):
    empty_file = tmp_path / "empty.docx"
    empty_file.touch()
    result = FileValidator.validate_file(empty_file)
    assert result.is_valid is False
    assert "kosong" in (result.error_message or "")


def test_validate_valid_csv(tmp_path):
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
    result = FileValidator.validate_file(csv_file)
    assert result.is_valid is True
    assert result.extension == ".csv"
    assert result.file_size_bytes > 0


def test_validate_corrupt_pdf(tmp_path):
    corrupt_pdf = tmp_path / "broken.pdf"
    corrupt_pdf.write_bytes(b"NOT_A_PDF_HEADER_123456")
    result = FileValidator.validate_file(corrupt_pdf)
    assert result.is_valid is False
    assert "tidak sesuai" in (result.error_message or "")

