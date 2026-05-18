from pathlib import Path
import json
import shutil
import uuid

from scripts.validate_excel_full_reader import validate_excel_full_reader, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"validate_excel_full_reader_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _base_reader_report() -> dict:
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
                "warnings": [],
                "manual_review": [],
                "risks": [],
            }
        ],
        "sheets": [
            {
                "sheet_ref": "data/samples/a.xlsx::Datos",
                "workbook_ref": "data/samples/a.xlsx",
                "sheet_name_sanitized": "Datos",
                "sheet_type": "WORKSHEET",
                "used_range": {"min_row": 1, "max_row": 2, "min_column": 1, "max_column": 3},
                "dimensions": {"max_row": 2, "max_column": 3},
                "visibility": {"sheet_state": "visible", "is_hidden": False, "is_very_hidden": False},
                "merged_cells_summary": {"count": 0, "ranges": []},
                "formulas_summary": {"count": 0, "sample_cells": []},
                "comments_summary": {"count": 0, "samples": []},
                "styles_summary": {"styled_cells": 0, "unique_style_ids": [], "unique_style_ids_count": 0, "top_style_ids": [], "style_vs_data_ratio": 0.0},
                "density_profile": {"non_empty_cells": 3, "used_cells_total": 6, "non_empty_pct": 50.0, "top_non_empty_rows": [], "top_non_empty_columns": []},
                "candidate_header_rows": [1],
                "candidate_columns": {"codigo": ["A"], "descripcion": ["B"], "unidad": ["C"], "cantidad": [], "precio": [], "importe": [], "capitulo": [], "partida": []},
                "candidate_table_blocks": [{"block_type": "heuristic_table_block", "header_row": 1, "range": {"min_row": 1, "max_row": 2, "min_column": 1, "max_column": 3}, "confidence": "heuristic", "source": "candidate_header_rows"}],
                "visual_blocks": [],
                "budget_signals": {"candidate_header_rows": [1], "candidate_columns": {"codigo": ["A"], "descripcion": ["B"], "unidad": ["C"], "cantidad": [], "precio": [], "importe": [], "capitulo": [], "partida": []}, "signals_by_field": {}},
                "traceability_map": [{"row": 1, "column": 1, "coordinate": "A1", "data_type": "s", "value_type": "str", "sanitized_value": "Codigo", "formula": None, "flags": []}],
                "cell_samples_sanitized": {"first_non_empty_rows": [{"row": 1, "cells": ["Codigo", "Descripcion", "Unidad"]}], "dense_rows": [], "possible_header_rows": [{"row": 1, "cells": ["Codigo", "Descripcion", "Unidad"]}]},
                "warnings": [],
                "manual_review": [],
                "is_empty_sheet": False,
                "is_likely_tabular": True,
                "unknown_or_unsupported": [],
            }
        ],
        "global_summary": {"traced_cells_total": 1},
        "risks": [],
        "warnings": [],
        "manual_review": [],
        "controlled_exclusions": [],
    }


def test_valid_reader_contract_ready_for_intermediate_normalization():
    report = validate_excel_full_reader(_base_reader_report(), "reader.json")
    assert report["validation_metadata"]["status"] == "VALID"
    assert report["validation_readiness"]["global"] == "VALIDATION_READY_FOR_INTERMEDIATE_NORMALIZATION"
    assert report["global_validation_summary"]["can_advance_to_excel_intermediate_normalization"] is True


def test_missing_root_key_blocks():
    payload = _base_reader_report()
    payload.pop("sheets")
    report = validate_excel_full_reader(payload, "reader.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_missing_workbook_traceability_blocks():
    payload = _base_reader_report()
    payload["sheets"][0]["traceability_map"] = []
    report = validate_excel_full_reader(payload, "reader.json")
    assert any(item["code"] == "TRACEABILITY_MAP_EMPTY" for item in report["blocking_errors"])


def test_chartsheet_is_preserved_as_manual_review():
    payload = _base_reader_report()
    payload["workbook_summaries"][0]["sheet_count"] = 2
    payload["workbook_summaries"][0]["chartsheet_count"] = 1
    payload["sheets"].append(
        {
            "sheet_ref": "data/samples/a.xlsx::Grafica",
            "workbook_ref": "data/samples/a.xlsx",
            "sheet_name_sanitized": "Grafica",
            "sheet_type": "CHARTSHEET",
            "used_range": {"min_row": None, "max_row": None, "min_column": None, "max_column": None},
            "dimensions": {"max_row": None, "max_column": None},
            "visibility": {"sheet_state": "visible", "is_hidden": False, "is_very_hidden": False},
            "merged_cells_summary": {"count": 0, "ranges": []},
            "formulas_summary": {"count": 0, "sample_cells": []},
            "comments_summary": {"count": 0, "samples": []},
            "styles_summary": {"styled_cells": 0, "unique_style_ids": [], "unique_style_ids_count": 0, "top_style_ids": [], "style_vs_data_ratio": 0.0},
            "density_profile": {"non_empty_cells": 0, "used_cells_total": 0, "non_empty_pct": 0.0, "top_non_empty_rows": [], "top_non_empty_columns": []},
            "candidate_header_rows": [],
            "candidate_columns": {"codigo": [], "descripcion": [], "unidad": [], "cantidad": [], "precio": [], "importe": [], "capitulo": [], "partida": []},
            "candidate_table_blocks": [],
            "visual_blocks": [{"block_type": "chartsheet_context"}],
            "budget_signals": {"candidate_header_rows": [], "candidate_columns": {"codigo": [], "descripcion": [], "unidad": [], "cantidad": [], "precio": [], "importe": [], "capitulo": [], "partida": []}, "signals_by_field": {}},
            "traceability_map": [],
            "cell_samples_sanitized": {"first_non_empty_rows": [], "dense_rows": [], "possible_header_rows": []},
            "warnings": ["CHARTSHEET_PRESENT"],
            "manual_review": ["CHARTSHEET_CONTEXT"],
            "is_empty_sheet": True,
            "is_likely_tabular": False,
            "unknown_or_unsupported": [],
        }
    )
    report = validate_excel_full_reader(payload, "reader.json")
    assert any(item["code"] == "CHARTSHEET_CONTEXT" for item in report["manual_review_items"])


def test_controlled_exclusions_can_still_advance():
    payload = _base_reader_report()
    payload["controlled_exclusions"] = [{"relative_path_sanitized": "data/samples/legacy.xls", "reason": "UNSUPPORTED_EXCEL_FORMAT"}]
    report = validate_excel_full_reader(payload, "reader.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS"
    assert report["global_validation_summary"]["controlled_exclusions_count"] == 1


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        report = validate_excel_full_reader(_base_reader_report(), "reader.json")
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "validation_metadata" in loaded
        assert "Excel Full Reader Validation Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_no_master_or_ratios_or_final_categories():
    report = validate_excel_full_reader(_base_reader_report(), "reader.json")
    serialized = json.dumps(report)
    assert "master_import" not in serialized
    assert '"ratios"' not in serialized
    assert '"ratio_calculation"' not in serialized
    assert "final_normalized_categories" not in serialized

