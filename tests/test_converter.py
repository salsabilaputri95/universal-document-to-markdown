"""Unit tests for ConversionManager and engine execution."""

from core.converter import ConversionManager


def test_convert_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Age,Role\nAlice,30,Developer\nBob,25,Designer\n", encoding="utf-8")

    mgr = ConversionManager()
    res = mgr.convert_file(csv_file, engine_choice="markitdown", output_dir=tmp_path / "out")

    assert res.success is True
    assert "Alice" in res.markdown_content
    assert "Developer" in res.markdown_content
    assert res.output_md_path is not None
    assert res.output_md_path.is_file()


def test_convert_xlsx_auto(tmp_path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Item", "Count"])
    ws.append(["Server", 4])
    xlsx_file = tmp_path / "servers.xlsx"
    wb.save(xlsx_file)
    wb.close()

    mgr = ConversionManager()
    res = mgr.convert_file(xlsx_file, engine_choice="auto", output_dir=tmp_path / "out")

    assert res.success is True
    assert "Server" in res.markdown_content
    assert res.used_engine == "ExcelProcessor"


def test_convert_invalid_file(tmp_path):
    fake_doc = tmp_path / "test.xyz"
    fake_doc.write_text("not supported")

    mgr = ConversionManager()
    res = mgr.convert_file(fake_doc, engine_choice="auto", output_dir=tmp_path / "out")

    assert res.success is False
    assert "tidak didukung" in (res.error_message or "")

