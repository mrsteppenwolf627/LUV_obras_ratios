from pathlib import Path
import shutil
import uuid

import pytest

from scripts.inspect_samples import build_sanitized_inventory, inspect_excel, inspect_samples


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"inspect_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_inspect_samples_empty():
    root = _make_root()
    try:
        (root / "data" / "samples").mkdir(parents=True)

        inventory = inspect_samples(root)

        assert inventory["exists"] is True
        assert inventory["files_count_total"] == 0
        assert inventory["sample_files_count"] == 0
        assert inventory["message"].startswith("No sample files")
    finally:
        _cleanup(root)


def test_inspect_samples_classification_and_hints():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)

        (samples / "presupuesto_final_v2.xls").write_text("not-real-excel", encoding="utf-8")
        (samples / "backup" / "mediciones.bc3").parent.mkdir(parents=True)
        (samples / "backup" / "mediciones.bc3").write_text("~K|sample", encoding="utf-8")
        (samples / "contrato.pdf").write_bytes(b"%PDF-1.4")
        (samples / ".gitkeep").write_text("", encoding="utf-8")

        inventory = inspect_samples(root)
        non_ignored = [item for item in inventory["files"] if not item["is_ignored"]]
        classes = {item["classification"] for item in non_ignored}

        assert inventory["files_count_total"] == 4
        assert inventory["sample_files_count"] == 3
        assert inventory["ignored_files_count"] == 1
        assert {"EXCEL", "BC3", "PDF"}.issubset(classes)

        excel_entry = next(i for i in non_ignored if i["extension"] == ".xls")
        assert excel_entry["version_or_phase_hint"] is True

        bc3_entry = next(i for i in non_ignored if i["extension"] == ".bc3")
        assert bc3_entry["backup_hint"] is True

        pdf_entry = next(i for i in non_ignored if i["extension"] == ".pdf")
        assert pdf_entry["inspection"]["status"] == "REFERENCE_ONLY_DIAGNOSTIC"

        gitkeep_entry = next(i for i in inventory["files"] if i["filename"] == ".gitkeep")
        assert gitkeep_entry["inspection"]["status"] == "IGNORED_SUPPORT_FILE"
    finally:
        _cleanup(root)


def test_sanitized_inventory_omits_sensitive_previews():
    inventory = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "samples_dir": "data/samples",
        "exists": True,
        "files_count_total": 2,
        "sample_files_count": 2,
        "ignored_files_count": 0,
        "message": "OK",
        "counts_by_class_total": {"EXCEL": 1, "BC3": 1},
        "counts_by_class": {"EXCEL": 1, "BC3": 1},
        "files": [
            {
                "relative_path": "data/samples/a.xlsx",
                "extension": ".xlsx",
                "size_bytes": 10,
                "classification": "EXCEL",
                "backup_hint": False,
                "version_or_phase_hint": False,
                "is_ignored": False,
                "inspection": {
                    "status": "EXCEL_INSPECTED_BASIC",
                    "sheet_names": ["A"],
                    "sheet_types": [{"sheet": "A", "sheet_type": "WORKSHEET"}],
                    "sheet_dimensions": [{"sheet": "A", "max_row": 10, "max_column": 5}],
                    "preview_headers": {"A": ["sensitive"]},
                },
            },
            {
                "relative_path": "data/samples/a.bc3",
                "extension": ".bc3",
                "size_bytes": 10,
                "classification": "BC3",
                "backup_hint": False,
                "version_or_phase_hint": False,
                "is_ignored": False,
                "inspection": {
                    "status": "BC3_INSPECTED_SUPERFICIAL",
                    "detected_encoding": "cp1252",
                    "is_text_like": True,
                    "line_sample": ["sensitive"],
                },
            },
        ],
    }
    sanitized = build_sanitized_inventory(inventory, [])

    excel_s = next(f for f in sanitized["files"] if f["classification"] == "EXCEL")
    bc3_s = next(f for f in sanitized["files"] if f["classification"] == "BC3")
    assert "preview_headers" not in excel_s["inspection"]
    assert "line_sample" not in bc3_s["inspection"]
    assert excel_s["inspection"]["sheet_count"] == 1


def test_inspect_excel_with_chartsheet_supported():
    openpyxl = pytest.importorskip("openpyxl")
    from openpyxl.chart import BarChart, Reference

    root = _make_root()
    try:
        workbook_path = root / "charts.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data"
        ws.append(["A", "B"])
        ws.append([1, 2])
        chart = BarChart()
        data = Reference(ws, min_col=2, min_row=1, max_row=2)
        chart.add_data(data, titles_from_data=True)
        cs = wb.create_chartsheet(title="Chart")
        cs.add_chart(chart)
        wb.save(workbook_path)
        wb.close()

        result = inspect_excel(workbook_path)
        sheet_types = {x["sheet"]: x["sheet_type"] for x in result["sheet_types"]}

        assert result["status"] == "EXCEL_INSPECTED_BASIC"
        assert sheet_types["Data"] == "WORKSHEET"
        assert sheet_types["Chart"] in {"CHARTSHEET", "UNKNOWN_SHEET_TYPE"}
    finally:
        _cleanup(root)
