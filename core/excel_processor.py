"""Excel processing engine using OpenPyXL and Pandas.

Handles multi-sheet workbooks, merged cells, cached formulas,
number/date formatting, and markdown table conversion.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl

from utils.logger import logger


class ExcelProcessor:
    """Processes Excel (.xlsx) spreadsheets into clean Markdown tables."""

    WIDE_TABLE_COLUMN_THRESHOLD = 20

    @classmethod
    def process_file(
        cls,
        file_path: Path | str,
        include_hidden_sheets: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        """Convert all worksheets of an Excel workbook to Markdown.

        Returns:
            Tuple of (markdown_string, metadata_dict)
        """
        path = Path(file_path)
        filename = path.name
        stem = path.stem

        wb_data = None
        wb_formula = None

        warnings: list[str] = []
        sheets_metadata: list[dict[str, Any]] = []
        markdown_sections: list[str] = [f"# {stem}\n"]

        try:
            # 1. Load data workbook (cached values)
            wb_data = openpyxl.load_workbook(
                path,
                data_only=True,
                read_only=False,
                keep_links=False,
            )

            # 2. Load formula workbook (to detect formula definitions if cached is missing)
            try:
                wb_formula = openpyxl.load_workbook(
                    path,
                    data_only=False,
                    read_only=True,
                    keep_links=False,
                )
            except Exception as f_err:
                logger.debug(f"Could not load formula view for {filename}: {f_err}")
                wb_formula = None

            total_sheets = len(wb_data.sheetnames)

            for sheet_name in wb_data.sheetnames:
                ws_data = wb_data[sheet_name]
                ws_formula = wb_formula[sheet_name] if wb_formula and sheet_name in wb_formula.sheetnames else None

                is_hidden = ws_data.sheet_state != "visible"
                if is_hidden and not include_hidden_sheets:
                    continue

                sheet_md, sheet_meta = cls._process_worksheet(
                    ws_data=ws_data,
                    ws_formula=ws_formula,
                    filename=filename,
                    is_hidden=is_hidden,
                )

                if sheet_meta.get("is_wide", False):
                    warning_msg = (
                        f"Worksheet '{sheet_name}' memiliki {sheet_meta['columns']} kolom "
                        f"(melebihi ambang batas {cls.WIDE_TABLE_COLUMN_THRESHOLD} kolom). "
                        "Tabel mungkin memerlukan scroll horizontal."
                    )
                    warnings.append(warning_msg)

                sheets_metadata.append(sheet_meta)
                markdown_sections.append(sheet_md)

        except Exception as err:
            logger.error(f"Error processing Excel file {filename}: {err}", exc_info=True)
            raise RuntimeError(f"Gagal memproses file Excel '{filename}': {err}") from err
        finally:
            if wb_data:
                wb_data.close()
            if wb_formula:
                wb_formula.close()

        combined_markdown = "\n\n".join(markdown_sections).strip()

        metadata: dict[str, Any] = {
            "filename": filename,
            "engine": "ExcelProcessor (OpenPyXL)",
            "total_sheets": total_sheets,
            "sheets": sheets_metadata,
            "warnings": warnings,
            "pages": total_sheets,
        }

        return combined_markdown, metadata

    @classmethod
    def _process_worksheet(
        cls,
        ws_data: openpyxl.worksheet.worksheet.Worksheet,
        ws_formula: Any,
        filename: str,
        is_hidden: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Process a single worksheet into a Markdown section."""
        sheet_name = ws_data.title
        max_row = ws_data.max_row or 0
        max_col = ws_data.max_column or 0

        # Handle empty sheet
        if max_row == 0 or max_col == 0:
            md_empty = (
                f"## Worksheet: {sheet_name}\n\n"
                f"*Status: {'Sheet Tersembunyi | ' if is_hidden else ''}Sheet Kosong (0 baris, 0 kolom)*\n"
            )
            meta_empty = {
                "sheet_name": sheet_name,
                "is_hidden": is_hidden,
                "rows": 0,
                "columns": 0,
                "is_empty": True,
                "is_wide": False,
            }
            return md_empty, meta_empty

        # Resolve merged cells map: (row, col) -> top_left_cell_value
        merged_values: dict[tuple[int, int], Any] = {}
        for merge_range in ws_data.merged_cells.ranges:
            top_left = ws_data.cell(row=merge_range.min_row, column=merge_range.min_col).value
            for r in range(merge_range.min_row, merge_range.max_row + 1):
                for c in range(merge_range.min_col, merge_range.max_col + 1):
                    if (r, c) != (merge_range.min_row, merge_range.min_col):
                        merged_values[(r, c)] = top_left

        # Read cell values grid
        grid: list[list[str]] = []
        col_is_numeric: list[bool] = [True] * max_col

        for r in range(1, max_row + 1):
            row_cells: list[str] = []
            has_row_content = False

            for c in range(1, max_col + 1):
                val = ws_data.cell(row=r, column=c).value

                # If None and inside merged range, inherit from top-left
                if val is None and (r, c) in merged_values:
                    val = merged_values[(r, c)]

                # Check formula fallback
                if val is None and ws_formula is not None:
                    try:
                        f_cell_val = ws_formula.cell(row=r, column=c).value
                        if isinstance(f_cell_val, str) and f_cell_val.startswith("="):
                            val = f"[Formula: {f_cell_val}]"
                    except Exception:
                        pass

                # Format formatted string
                formatted_str = cls._format_cell_value(val)
                if formatted_str:
                    has_row_content = True
                    # Check if numeric for column alignment
                    if r > 1 and not cls._is_numeric_str(formatted_str):
                        col_is_numeric[c - 1] = False

                row_cells.append(formatted_str)

            if has_row_content:
                grid.append(row_cells)

        # Re-check actual content rows
        actual_rows = len(grid)
        if actual_rows == 0:
            md_empty = (
                f"## Worksheet: {sheet_name}\n\n"
                f"*Status: {'Sheet Tersembunyi | ' if is_hidden else ''}Sheet Kosong (0 baris, 0 data)*\n"
            )
            meta_empty = {
                "sheet_name": sheet_name,
                "is_hidden": is_hidden,
                "rows": 0,
                "columns": max_col,
                "is_empty": True,
                "is_wide": max_col > cls.WIDE_TABLE_COLUMN_THRESHOLD,
            }
            return md_empty, meta_empty

        # Build Markdown Table
        header_row = grid[0]
        # Clean header: ensure no empty headers
        cleaned_headers = [
            h if h.strip() else f"Kolom {idx + 1}"
            for idx, h in enumerate(header_row)
        ]

        # Alignment separators
        alignments = []
        for is_num in col_is_numeric:
            alignments.append("---:" if is_num else ":---")

        table_lines = [
            "| " + " | ".join(cls._escape_markdown_pipe(h) for h in cleaned_headers) + " |",
            "| " + " | ".join(alignments) + " |",
        ]

        for data_row in grid[1:]:
            row_str = "| " + " | ".join(cls._escape_markdown_pipe(c) for c in data_row) + " |"
            table_lines.append(row_str)

        info_header = [f"## Worksheet: {sheet_name}"]
        status_items = [
            f"**File**: `{filename}`",
            f"**Worksheet**: `{sheet_name}`",
            f"**Baris**: {actual_rows}",
            f"**Kolom**: {max_col}",
        ]
        if is_hidden:
            status_items.append("*(Sheet Tersembunyi)*")

        md_output = (
            "\n".join(info_header)
            + "\n"
            + " | ".join(status_items)
            + "\n\n"
            + "\n".join(table_lines)
        )

        is_wide = max_col > cls.WIDE_TABLE_COLUMN_THRESHOLD
        sheet_meta = {
            "sheet_name": sheet_name,
            "is_hidden": is_hidden,
            "rows": actual_rows,
            "columns": max_col,
            "is_empty": False,
            "is_wide": is_wide,
        }

        return md_output, sheet_meta

    @staticmethod
    def _format_cell_value(value: Any) -> str:
        """Format an Excel cell value into a clean string."""
        if value is None:
            return ""
        if isinstance(value, (datetime, date)):
            if isinstance(value, datetime) and (value.hour or value.minute or value.second):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return value.strftime("%Y-%m-%d")
        if isinstance(value, float):
            # If float is an integer value, show as int
            if value.is_integer():
                return str(int(value))
            return f"{value:.4f}".rstrip("0").rstrip(".")
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        # String or other
        return str(value).strip().replace("\r\n", " ").replace("\n", " ")

    @staticmethod
    def _escape_markdown_pipe(text: str) -> str:
        """Escape pipe character inside markdown table cells."""
        return text.replace("|", "\\|")

    @staticmethod
    def _is_numeric_str(s: str) -> bool:
        """Check if string looks like a numeric value."""
        if not s:
            return True
        # Strip currency symbols and commas
        cleaned = s.replace(",", "").replace(".", "").replace("$", "").replace("Rp", "").strip()
        return cleaned.lstrip("-+").isdigit()

