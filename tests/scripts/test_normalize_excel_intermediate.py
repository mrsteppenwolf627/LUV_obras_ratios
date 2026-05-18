from pathlib import Path
import json
import shutil
import uuid

from scripts.normalize_excel_intermediate import normalize_excel_intermediate, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"normalize_excel_intermediate_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _reader_report() -> dict:
    return {
        "reader_metadata": {"generated_at": "2026-05-18T00:00:00Z"},
        "source_files": [{"relative_path_sanitized": "data/samples/a.xlsx", "extension": ".xlsx"}],
        "workbook_summaries": [
            {
                "workbook_ref": "data/samples/a.xlsx",
                "relative_path_sanitized": "data/samples/a.xlsx",
                "extension": ".xlsx",
                "sheet_count": 1,
                "worksheet_count": 1,
                "chartsheet_count": 0,
                "readable": True,
                "errors": [],
                "warnings": ["FORMULAS_PRESENT"],
                "manual_review": ["NO_CLEAR_HEADERS:Datos"],
                "risks": [],
            }
        ],
        "sheets": [
            {
                "sheet_ref": "data/samples/a.xlsx::Datos",
                "workbook_ref": "data/samples/a.xlsx",
                "sheet_name_sanitized": "Datos",
                "sheet_type": "WORKSHEET",
                "used_range": {"min_row": 1, "max_row": 3, "min_column": 1, "max_column": 4},
                "dimensions": {"max_row": 3, "max_column": 4},
                "visibility": {"sheet_state": "visible", "is_hidden": False, "is_very_hidden": False},
                "merged_cells_summary": {"count": 0, "ranges": []},
                "formulas_summary": {"count": 1, "sample_cells": ["D2"]},
                "comments_summary": {"count": 1, "samples": [{"coordinate": "B2", "author": "Codex", "text": "Comentario"}]},
                "styles_summary": {"styled_cells": 2, "unique_style_ids": [1], "unique_style_ids_count": 1, "top_style_ids": [{"style_id": 1, "count": 2}], "style_vs_data_ratio": 1.0},
                "density_profile": {"non_empty_cells": 6, "used_cells_total": 12, "non_empty_pct": 50.0, "top_non_empty_rows": [], "top_non_empty_columns": []},
                "candidate_header_rows": [1],
                "candidate_columns": {"codigo": ["A"], "descripcion": ["B"], "unidad": ["C"], "cantidad": ["D"], "precio": ["E"], "importe": ["F"], "capitulo": ["G"], "partida": ["H"]},
                "candidate_table_blocks": [{"block_type": "heuristic_table_block", "header_row": 1, "range": {"min_row": 1, "max_row": 3, "min_column": 1, "max_column": 4}, "confidence": "heuristic", "source": "candidate_header_rows"}],
                "visual_blocks": [{"block_type": "merged_cells", "count": 1, "ranges": ["A1:C1"]}],
                "budget_signals": {"candidate_header_rows": [1], "candidate_columns": {"codigo": ["A"], "descripcion": ["B"], "unidad": ["C"], "cantidad": ["D"], "precio": ["E"], "importe": ["F"], "capitulo": ["G"], "partida": ["H"]}, "signals_by_field": {}},
                "traceability_map": [
                    {"row": 1, "column": 1, "coordinate": "A1", "data_type": "s", "value_type": "str", "sanitized_value": "Codigo", "formula": None, "flags": []},
                    {"row": 2, "column": 4, "coordinate": "D2", "data_type": "f", "value_type": "str", "sanitized_value": "=SUM(A1:A2)", "formula": "=SUM(A1:A2)", "flags": ["FORMULA"]},
                    {"row": 2, "column": 2, "coordinate": "B2", "data_type": "s", "value_type": "str", "sanitized_value": "Texto", "formula": None, "flags": ["COMMENT"]},
                ],
                "cell_samples_sanitized": {
                    "first_non_empty_rows": [{"row": 1, "cells": ["Codigo", "Descripcion", "Unidad"]}],
                    "dense_rows": [{"row": 2, "non_empty_cells": 4, "cells": ["A1", "Texto", "m2", "=SUM(A1:A2)"]}],
                    "possible_header_rows": [{"row": 1, "cells": ["Codigo", "Descripcion", "Unidad"]}],
                },
                "warnings": ["FORMULAS_PRESENT"],
                "manual_review": ["NO_CLEAR_HEADERS:Datos"],
                "is_empty_sheet": False,
                "is_likely_tabular": True,
                "unknown_or_unsupported": [{"block_type": "visual_note", "note": "alpha"}],
            }
        ],
        "global_summary": {"traced_cells_total": 3},
        "risks": [],
        "warnings": ["FORMULAS_PRESENT"],
        "manual_review": ["NO_CLEAR_HEADERS:Datos"],
        "controlled_exclusions": [{"relative_path_sanitized": "data/samples/legacy.xls", "reason": "UNSUPPORTED_EXCEL_FORMAT"}],
    }


def _validation_report() -> dict:
    return {
        "sheet_validation": [
            {
                "sheet_ref": "data/samples/a.xlsx::Datos",
                "warnings": [{"code": "NON_TABULAR_WORKSHEET", "detail": "Manual check"}],
                "manual_review": [{"code": "CHARTSHEET_CONTEXT", "detail": "N/A"}],
            }
        ]
    }


def test_normalizes_reader_output_to_intermediate_structure():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    assert report["global_summary"]["normalized_workbooks_count"] == 1
    assert report["workbooks"][0]["workbook_ref"] == "data/samples/a.xlsx"
    sheet = report["workbooks"][0]["sheets"][0]
    assert sheet["candidate_tables"]
    assert sheet["candidate_rows"]
    assert sheet["source_trace"]["cell_traceability"]
    assert sheet["candidate_chapters"]
    assert sheet["candidate_cost_items"]


def test_preserves_units_and_signals_without_final_normalization():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    sheet = report["workbooks"][0]["sheets"][0]
    assert "C" in [item.get("column") for item in sheet["unit_signals"] if "column" in item]
    assert sheet["quantity_signals"]
    assert sheet["price_signals"]
    assert sheet["amount_signals"]


def test_preserves_formula_signals_and_unknown_blocks():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    sheet = report["workbooks"][0]["sheets"][0]
    assert sheet["formula_signals"]
    assert sheet["unknown_or_unstructured_blocks"]


def test_preserves_manual_review_and_warnings():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    sheet = report["workbooks"][0]["sheets"][0]
    assert any("NO_CLEAR_HEADERS" in item for item in sheet["manual_review"])
    assert any("FORMULAS_PRESENT" in item for item in sheet["warnings"])


def test_source_trace_keeps_cell_level_traceability():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    trace = report["workbooks"][0]["sheets"][0]["source_trace"]
    assert trace["traceability_count"] == 3
    assert any(item["coordinate"] == "D2" for item in trace["cell_traceability"])


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        report = normalize_excel_intermediate(_reader_report(), _validation_report())
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "normalization_metadata" in loaded
        assert "Excel Intermediate Normalization Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_no_master_or_ratios_or_final_categories_or_mapping():
    report = normalize_excel_intermediate(_reader_report(), _validation_report())
    serialized = json.dumps(report)
    assert "master_import" not in serialized
    assert '"ratios"' not in serialized
    assert "final_normalized_categories" not in serialized
    assert "CATEGORY_MAPPING" not in serialized


def test_input_not_modified():
    reader = _reader_report()
    validation = _validation_report()
    before_reader = json.dumps(reader, sort_keys=True)
    before_validation = json.dumps(validation, sort_keys=True)
    _ = normalize_excel_intermediate(reader, validation)
    assert json.dumps(reader, sort_keys=True) == before_reader
    assert json.dumps(validation, sort_keys=True) == before_validation
