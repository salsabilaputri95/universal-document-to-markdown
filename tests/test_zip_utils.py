"""Unit tests for ZIP packaging and Export Manager."""

from core.converter import ConversionResult
from core.export_manager import ExportManager
from utils.zip_utils import create_export_zip, verify_zip_integrity


def test_zip_creation_and_integrity(tmp_path):
    zip_dest = tmp_path / "test_bundle.zip"
    markdown_files = {
        "doc1.md": "# Doc 1\nContent 1",
        "doc2.md": "# Doc 2\nContent 2",
    }
    # Create fake asset folder
    assets_dir = tmp_path / "doc1_assets"
    assets_dir.mkdir()
    (assets_dir / "image_001.png").write_bytes(b"\x89PNG\r\n\x1a\nfakeimage")

    asset_dirs = {"doc1_assets": assets_dir}
    meta = {"source": "test_suite", "count": 2}

    success = create_export_zip(
        zip_dest_path=zip_dest,
        markdown_files=markdown_files,
        asset_dirs=asset_dirs,
        metadata=meta,
    )
    assert success is True
    assert zip_dest.is_file()

    valid, msg = verify_zip_integrity(zip_dest)
    assert valid is True


def test_export_manager_batch_zip(tmp_path):
    res1 = ConversionResult(
        success=True,
        filename="report.docx",
        extension=".docx",
        file_size_bytes=1024,
        file_size_formatted="1.00 KB",
        requested_engine="auto",
        used_engine="Docling",
        markdown_content="# Report\nHello from docx",
    )
    res2 = ConversionResult(
        success=False,
        filename="corrupted.pdf",
        extension=".pdf",
        file_size_bytes=512,
        file_size_formatted="512 B",
        requested_engine="auto",
        used_engine="Docling",
        error_message="Bad format",
    )

    zip_file = ExportManager.create_batch_zip(
        results=[res1, res2],
        zip_filename="export_test.zip",
        output_dir=tmp_path,
    )
    assert zip_file.is_file()
    valid, _ = verify_zip_integrity(zip_file)
    assert valid is True

