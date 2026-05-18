from pathlib import Path
import json
import shutil
import uuid

from scripts.validate_bc3_intermediate_normalization import (
    validate_intermediate_normalization,
    write_outputs,
)


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"validate_bc3_intermediate_normalization_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _valid_fixture() -> dict:
    return {
        "normalization_metadata": {"generated_at": "2026-05-18T00:00:00Z"},
        "source_reports": {"strict_parse": "x", "strict_validation": "y"},
        "corpus_status": {
            "full_corpus_status": "NOT_BLOCKED",
            "valid_subset_status": "ADVANCE_ALLOWED",
            "can_advance_with_valid_subset": True,
        },
        "files": [
            {
                "file_ref": {"sanitized_id": "BC3_01", "relative_path": "data/samples/a.bc3"},
                "source_trace": {"header_line": 1},
                "chapters": [{"code": "CAP01#"}],
                "cost_items": [{"code": "IT01"}],
                "relations": [{"parent_code": "CAP01#", "child_code": "IT01", "line_number": 10}],
                "units": ["M2"],
                "descriptions": [{"code": "IT01", "text": "Item"}],
                "measurement_signals": [{"code": "IT01", "tokens": ["M2"], "consolidated": False}],
                "economic_signals": [{"code": "IT01", "tokens": ["EUR"], "consolidated": False}],
                "validation_flags": {"strict_parse_warnings": []},
                "manual_review": ["CHECK_UNIT"],
                "unknown_or_unsupported": {"unknown": [], "unsupported": []},
            }
        ],
        "global_summary": {"files_total": 1, "eligible_files_count": 1, "excluded_files_count": 0},
        "controlled_exclusions": [
            {
                "sanitized_id": "BC3_02",
                "file_eligibility_status": "NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT",
            }
        ],
    }


def test_valid_normalization_contract():
    report = validate_intermediate_normalization(_valid_fixture(), "fixture.json")
    assert report["global_validation_summary"]["contract_status"] == "VALID"


def test_missing_normalization_metadata():
    fixture = _valid_fixture()
    fixture.pop("normalization_metadata")
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "MISSING_NORMALIZATION_METADATA" for item in report["blocking_errors"])


def test_missing_files_key():
    fixture = _valid_fixture()
    fixture.pop("files")
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "MISSING_FILES" for item in report["blocking_errors"])


def test_missing_source_trace():
    fixture = _valid_fixture()
    fixture["files"][0].pop("source_trace")
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "MISSING_SOURCE_TRACE" for item in report["blocking_errors"])


def test_chapters_not_list():
    fixture = _valid_fixture()
    fixture["files"][0]["chapters"] = {}
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "INVALID_CHAPTERS_TYPE" for item in report["blocking_errors"])


def test_cost_items_not_list():
    fixture = _valid_fixture()
    fixture["files"][0]["cost_items"] = {}
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "INVALID_COST_ITEMS_TYPE" for item in report["blocking_errors"])


def test_relation_without_traceability():
    fixture = _valid_fixture()
    fixture["files"][0]["relations"] = [{"parent_code": "A", "child_code": "B"}]
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "RELATION_TRACEABILITY_MISSING" for item in report["blocking_errors"])


def test_economic_signal_consolidated_error():
    fixture = _valid_fixture()
    fixture["files"][0]["economic_signals"][0]["consolidated"] = True
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "ECONOMIC_SIGNAL_CONSOLIDATED_FORBIDDEN" for item in report["blocking_errors"])


def test_measurement_signal_consolidated_error():
    fixture = _valid_fixture()
    fixture["files"][0]["measurement_signals"][0]["consolidated"] = True
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "MEASUREMENT_SIGNAL_CONSOLIDATED_FORBIDDEN" for item in report["blocking_errors"])


def test_master_field_present_error():
    fixture = _valid_fixture()
    fixture["master_import_payload"] = {"x": 1}
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "FORBIDDEN_FIELD_PRESENT" for item in report["blocking_errors"])


def test_ratio_field_present_error():
    fixture = _valid_fixture()
    fixture["files"][0]["ratio_calculation"] = 10
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "FORBIDDEN_FIELD_PRESENT" for item in report["blocking_errors"])


def test_final_category_present_error():
    fixture = _valid_fixture()
    fixture["files"][0]["final_category"] = "x"
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "FORBIDDEN_FIELD_PRESENT" for item in report["blocking_errors"])


def test_category_mapping_present_error():
    fixture = _valid_fixture()
    fixture["CATEGORY_MAPPING"] = {"a": "b"}
    report = validate_intermediate_normalization(fixture, "fixture.json")
    assert any(item["code"] == "FORBIDDEN_FIELD_PRESENT" for item in report["blocking_errors"])


def test_controlled_exclusions_preserved():
    report = validate_intermediate_normalization(_valid_fixture(), "fixture.json")
    assert any(item["code"] == "CONTROLLED_EXCLUSIONS_PRESERVED" for item in report["info"])


def test_manual_review_preserved():
    report = validate_intermediate_normalization(_valid_fixture(), "fixture.json")
    assert any(item["code"] == "MANUAL_REVIEW_PRESERVED" for item in report["manual_review_items"])


def test_json_output_generated():
    root = _make_root()
    try:
        report = validate_intermediate_normalization(_valid_fixture(), "fixture.json")
        json_path, _ = write_outputs(root, report)
        assert json_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "validation_metadata" in loaded
    finally:
        _cleanup(root)


def test_markdown_output_generated():
    root = _make_root()
    try:
        report = validate_intermediate_normalization(_valid_fixture(), "fixture.json")
        _, md_path = write_outputs(root, report)
        assert md_path.exists()
        assert "BC3 Intermediate Normalization Validation Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_input_not_modified():
    fixture = _valid_fixture()
    before = json.dumps(fixture, sort_keys=True)
    _ = validate_intermediate_normalization(fixture, "fixture.json")
    assert json.dumps(fixture, sort_keys=True) == before
