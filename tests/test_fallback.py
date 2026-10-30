"""Unit tests for fallback mechanism."""

from unittest.mock import MagicMock

from core.converter import ConversionManager


def test_converter_docling_fallback_to_markitdown(tmp_path):
    csv_file = tmp_path / "fallback_sample.csv"
    csv_file.write_text("item,qty\nWidget,50\n", encoding="utf-8")

    mgr = ConversionManager()

    # Mock Docling engine to raise an error
    mock_docling = MagicMock()
    mock_docling.convert.side_effect = RuntimeError("Simulated Docling CUDA/OOM failure")
    mgr._docling = mock_docling

    # Request docling engine explicitly
    res = mgr.convert_file(
        file_path=csv_file,
        engine_choice="docling",
        output_dir=tmp_path / "out",
    )

    # Verify fallback succeeded
    assert res.success is True
    assert res.fallback_used is True
    assert "Simulated Docling" in (res.fallback_reason or "")
    assert res.used_engine == "MarkItDown (Fallback)"
    assert "Widget" in res.markdown_content
