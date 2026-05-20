from pathlib import Path
import re
import shutil
import uuid

from openpyxl import Workbook, load_workbook

from scripts.generate_live_excel_master import generate_preview_from_real_xlsx, validate_workbook_file


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"live_master_prof_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _build_synthetic_budget(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Presupuesto"
    ws.append(["Resumen presupuesto obra"])
    ws.append(["Codigo", "Descripcion", "Ud", "Cantidad", "Precio Unitario", "Importe"])
    ws.append(["1", "MOVIMIENTO DE TIERRAS", "", "", "", ""])
    ws.append(["1.1.01", "Excavacion de zanjas", "m3", 10, 30, ""])
    ws.append(["1.1.02", "Relleno compactado", "m3", 5, 20, 100])
    ws.append(["2", "CIMENTACION", "", "", "", ""])
    ws.append(["2.1.01", "Hormigon en masa", "m3", 2, 120, ""])
    ws.append(["2.1.02", "Acero corrugado", "", "", "", 350])
    wb.save(path)
    wb.close()


def _first_review_and_trace(workbook: object) -> tuple[str, str]:
    review = next(name for name in workbook.sheetnames if name.startswith("BUDGET_REVIEW_") and not name.startswith("BUDGET_REVIEW_TRACE_"))
    trace = next(name for name in workbook.sheetnames if name.startswith("BUDGET_REVIEW_TRACE_"))
    return review, trace


def test_professional_review_sheet_structure_and_order():
    root = _make_root()
    try:
        src = root / "input.xlsx"
        _build_synthetic_budget(src)
        out = root / "outputs" / "live_excel_master" / "preview" / "preview.xlsx"
        generate_preview_from_real_xlsx(src, out, source_file_id="sf_prof_test_001")

        wb = load_workbook(out)
        try:
            review_name, trace_name = _first_review_and_trace(wb)
            assert wb.sheetnames[0] == "INDEX"
            assert wb.sheetnames[1] == review_name
            assert wb.sheetnames[2] == trace_name

            review_ws = wb[review_name]
            visible_headers = [review_ws.cell(row=4, column=idx).value for idx in range(1, 7)]
            assert visible_headers == ["Codigo", "Descripcion", "Ud", "Cantidad", "Precio unitario", "Importe"]
            assert review_ws.column_dimensions["G"].hidden is True
            assert review_ws.freeze_panes == "A5"
            assert review_ws["A4"].font.bold is True
            assert review_ws.column_dimensions["B"].width >= 40
            assert review_ws.auto_filter.ref == "A4:F4"

            hidden_header = review_ws.cell(row=4, column=7).value
            assert hidden_header == "_review_row_id"
            assert "source_file_id" not in visible_headers
            assert "import_batch_id" not in visible_headers
            assert "budget_version_id" not in visible_headers
            assert "source_row_number" not in visible_headers
            assert "mapping_confidence" not in visible_headers

            trace_ws = wb[trace_name]
            trace_headers = [trace_ws.cell(row=1, column=idx).value for idx in range(1, trace_ws.max_column + 1)]
            assert "review_row_id" in trace_headers
            assert "source_sheet_name" in trace_headers
            assert "source_row_number" in trace_headers
            assert "preserved_row_id" in trace_headers
            assert "cost_item_id" in trace_headers
        finally:
            wb.close()
        validate_workbook_file(out)
    finally:
        _cleanup(root)


def test_professional_review_formulas_and_hierarchy():
    root = _make_root()
    try:
        src = root / "input.xlsx"
        _build_synthetic_budget(src)
        out = root / "outputs" / "live_excel_master" / "preview" / "preview.xlsx"
        generate_preview_from_real_xlsx(src, out, source_file_id="sf_prof_test_002")
        wb = load_workbook(out)
        try:
            review_name, trace_name = _first_review_and_trace(wb)
            review_ws = wb[review_name]

            code_to_row: dict[str, int] = {}
            subtotal_rows: list[int] = []
            total_row = 0
            for row_idx in range(5, review_ws.max_row + 1):
                code = str(review_ws.cell(row=row_idx, column=1).value or "").strip()
                desc = str(review_ws.cell(row=row_idx, column=2).value or "").strip().upper()
                if code:
                    code_to_row[code] = row_idx
                if desc.startswith("SUBTOTAL"):
                    subtotal_rows.append(row_idx)
                if desc == "TOTAL GENERAL":
                    total_row = row_idx

            assert "1" in code_to_row
            assert "1.1.01" in code_to_row
            assert "2" in code_to_row
            assert total_row > 0
            assert len(subtotal_rows) >= 2
            assert code_to_row["1"] < code_to_row["1.1.01"] < subtotal_rows[0]

            first_item_amount = review_ws.cell(row=code_to_row["1.1.01"], column=6).value
            assert isinstance(first_item_amount, str) and first_item_amount.startswith("=")

            amount_only_value = review_ws.cell(row=code_to_row["2.1.02"], column=6).value
            assert not (isinstance(amount_only_value, str) and amount_only_value.startswith("="))
            assert float(amount_only_value) == 350.0

            for row_idx in subtotal_rows:
                subtotal_formula = review_ws.cell(row=row_idx, column=6).value
                assert isinstance(subtotal_formula, str) and subtotal_formula.startswith("=")

            total_formula = review_ws.cell(row=total_row, column=6).value
            assert isinstance(total_formula, str) and total_formula.startswith("=")
            assert review_ws.cell(row=total_row, column=2).font.bold is True

            trace_ws = wb[trace_name]
            trace_ids = {
                str(trace_ws.cell(row=row_idx, column=1).value or "").strip()
                for row_idx in range(2, trace_ws.max_row + 1)
            }
            assert trace_ids
            for row_idx in range(5, review_ws.max_row + 1):
                review_row_id = str(review_ws.cell(row=row_idx, column=7).value or "").strip()
                assert review_row_id
                match = re.search(r"(brv_[0-9a-f]+)$", review_row_id)
                assert match is not None
                assert match.group(1) in trace_ids
        finally:
            wb.close()
    finally:
        _cleanup(root)
