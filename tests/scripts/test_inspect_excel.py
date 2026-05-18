from pathlib import Path
import json
import shutil
import uuid

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.worksheet.table import Table, TableStyleInfo

from scripts.inspect_excel import inspect_excel_file, inspect_excel_samples, write_reports


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"inspect_excel_{uuid.uuid4().hex}"
    (root / "data" / "samples").mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_workbook_with_worksheet_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Datos"
        ws["A1"] = "codigo"
        ws["B1"] = "descripcion"
        ws["A2"] = "IT01"
        ws["B2"] = "Partida"
        file_path = root / "data" / "samples" / "a.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/a.xlsx")
        assert result["workbook_status"] == "EXCEL_DIAGNOSED"
        assert result["summary"]["worksheets_count"] == 1
    finally:
        _cleanup(root)


def test_workbook_with_chartsheet_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Base"
        ws.append(["x", "y"])
        ws.append([1, 2])
        ws.append([2, 3])
        chart = BarChart()
        data = Reference(ws, min_col=2, min_row=1, max_row=3)
        chart.add_data(data, titles_from_data=True)
        ch = wb.create_chartsheet(title="Grafica")
        ch.add_chart(chart)
        file_path = root / "data" / "samples" / "chart.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/chart.xlsx")
        assert result["summary"]["chartsheets_count"] == 1
        assert any(s["sheet_type"] == "CHARTSHEET" for s in result["sheets"])
    finally:
        _cleanup(root)


def test_empty_sheet_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Vacia"
        file_path = root / "data" / "samples" / "empty.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/empty.xlsx")
        sheet = next(s for s in result["sheets"] if s["sheet_name"] == "Vacia")
        assert sheet["is_empty_sheet"] is True
    finally:
        _cleanup(root)


def test_simple_table_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["codigo", "descripcion"])
        ws.append(["IT01", "A"])
        ws.append(["IT02", "B"])
        tab = Table(displayName="Tabla1", ref="A1:B3")
        style = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
        tab.tableStyleInfo = style
        ws.add_table(tab)
        file_path = root / "data" / "samples" / "table.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/table.xlsx")
        sheet = result["sheets"][0]
        assert "Tabla1" in sheet["possible_tables"]
    finally:
        _cleanup(root)


def test_candidate_headers_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["Codigo", "Descripcion", "Unidad", "Cantidad", "Precio", "Importe"])
        ws.append(["IT01", "Desc", "m2", 10, 20, 200])
        file_path = root / "data" / "samples" / "headers.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/headers.xlsx")
        headers = result["sheets"][0]["candidate_headers"]
        assert "Codigo" in headers
        assert "Importe" in headers
    finally:
        _cleanup(root)


def test_candidate_amount_price_quantity_columns_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["Cantidad", "Precio Unitario", "Importe"])
        ws.append([5, 2.5, 12.5])
        file_path = root / "data" / "samples" / "cols.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/cols.xlsx")
        cols = result["sheets"][0]["candidate_columns"]
        assert cols["cantidad"]
        assert cols["precio"]
        assert cols["importe"]
    finally:
        _cleanup(root)


def test_formulas_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["a", "b", "importe"])
        ws.append([2, 3, "=A2*B2"])
        file_path = root / "data" / "samples" / "formula.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/formula.xlsx")
        assert result["sheets"][0]["formula_cells_count"] == 1
    finally:
        _cleanup(root)


def test_merged_cells_detected():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Codigo"
        ws.merge_cells("A1:B1")
        file_path = root / "data" / "samples" / "merged.xlsx"
        wb.save(file_path)

        result = inspect_excel_file(file_path, "data/samples/merged.xlsx")
        assert result["sheets"][0]["merged_cells_count"] == 1
    finally:
        _cleanup(root)


def test_does_not_modify_input_file():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["Codigo", "Descripcion"])
        ws.append(["IT01", "Desc"])
        file_path = root / "data" / "samples" / "stable.xlsx"
        wb.save(file_path)
        before = file_path.read_bytes()

        _ = inspect_excel_file(file_path, "data/samples/stable.xlsx")
        after = file_path.read_bytes()

        assert before == after
    finally:
        _cleanup(root)


def test_inventory_and_reports_generation():
    root = _make_root()
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(["Codigo", "Descripcion"])
        ws.append(["IT01", "Desc"])
        wb.save(root / "data" / "samples" / "inv.xlsx")

        payload = inspect_excel_samples(root)
        json_path, md_path = write_reports(root, payload)

        assert payload["excel_files_detected"] == 1
        assert json.loads(json_path.read_text(encoding="utf-8"))["excel_files_detected"] == 1
        assert "Excel Diagnostics Inventory" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)
