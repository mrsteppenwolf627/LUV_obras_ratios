from pathlib import Path
import json
import shutil
import uuid

from scripts.normalize_bc3_intermediate import normalize_intermediate, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"normalize_bc3_intermediate_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _strict_parse_fixture() -> dict:
    return {
        "metadata": {"parser_stage": "strict"},
        "files": [
            {
                "file_ref": {
                    "sanitized_id": "BC3_01",
                    "relative_path": "data/samples/a.bc3",
                    "extension": ".bc3",
                    "size_bytes": 123,
                },
                "parsed": {
                    "header": {"line_number": 1, "raw": "~V|FIEBDC-3/2020"},
                    "concepts": [
                        {"line_number": 2, "record_type": "~C", "code": "CAP01#"},
                        {"line_number": 3, "record_type": "~C", "code": "IT01"},
                    ],
                    "relations": [
                        {
                            "line_number": 4,
                            "record_type": "~D",
                            "parent_code": "CAP01#",
                            "child_code": "IT01",
                        }
                    ],
                },
                "unknown": [{"line_number": 5, "raw": "~!|foo", "reason": "malformed"}],
                "unsupported": [{"line_number": 6, "record_type": "~K", "raw": "~K|bar"}],
                "errors": [],
                "warnings": ["ENCODING_MEDIUM_CONFIDENCE"],
                "manual_review_required": ["MULTIPLE_UNITS_NON_BLOCKING"],
                "traceability": {"lines_processed": 6, "parsed_records_count": 4},
            }
        ],
        "controlled_exclusions": [
            {
                "sanitized_id": "BC3_02",
                "relative_path": "data/samples/excluded.bc3",
                "file_eligibility_status": "NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT",
                "file_eligibility_reason": "Decode failure",
            }
        ],
        "global_summary": {
            "files_total": 2,
            "eligible_files_count": 1,
            "excluded_files_count": 1,
            "structurally_blocked_count": 0,
            "full_corpus_status": "NOT_BLOCKED",
            "valid_subset_status": "ADVANCE_ALLOWED",
            "can_advance_with_valid_subset": True,
        },
    }


def _strict_validation_fixture() -> dict:
    return {
        "files": [
            {
                "sanitized_id": "BC3_01",
                "status": "MANUAL_REVIEW_REQUIRED",
                "validation_readiness": "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW",
                "errors": [],
                "manual_review_items": [
                    {"code": "RELATION_ORPHAN_CHILD_NON_BLOCKING", "detail": "1/4 orphan relations ratio=0.25"}
                ],
            }
        ],
        "global_validation_summary": {
            "full_corpus_status": "NOT_BLOCKED",
            "valid_subset_status": "ADVANCE_ALLOWED",
            "can_advance_with_valid_subset": True,
        },
    }


def test_normalizes_eligible_file():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    assert report["global_summary"]["normalized_files_count"] == 1
    assert report["files"][0]["file_ref"]["sanitized_id"] == "BC3_01"


def test_preserves_controlled_exclusion():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    assert len(report["controlled_exclusions"]) == 1
    assert report["controlled_exclusions"][0]["sanitized_id"] == "BC3_02"


def test_generates_candidate_chapters():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    assert report["files"][0]["chapters"][0]["code"] == "CAP01#"


def test_generates_candidate_cost_items():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    assert report["files"][0]["cost_items"][0]["code"] == "IT01"


def test_preserves_relations():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    rel = report["files"][0]["relations"][0]
    assert rel["parent_code"] == "CAP01#"
    assert rel["child_code"] == "IT01"


def test_preserves_units_without_final_normalization():
    fixture = _strict_parse_fixture()
    fixture["files"][0]["parsed"]["concepts"][1]["code"] = "IT01 UD"
    report = normalize_intermediate(fixture, _strict_validation_fixture())
    assert "UD" in report["files"][0]["units"]


def test_preserves_and_sanitizes_descriptions():
    fixture = _strict_parse_fixture()
    long_code = "X" * 500
    fixture["files"][0]["parsed"]["concepts"][1]["code"] = long_code
    report = normalize_intermediate(fixture, _strict_validation_fixture())
    desc = report["files"][0]["descriptions"][1]
    assert len(desc["text"]) <= 400


def test_preserves_economic_signals_without_consolidation():
    fixture = _strict_parse_fixture()
    fixture["files"][0]["parsed"]["concepts"][1]["code"] = "IT01 EUR 120.50"
    report = normalize_intermediate(fixture, _strict_validation_fixture())
    signal = report["files"][0]["economic_signals"][1]
    assert "EUR" in signal["tokens"]
    assert signal["consolidated"] is False


def test_preserves_measurement_signals_without_consolidation():
    fixture = _strict_parse_fixture()
    fixture["files"][0]["parsed"]["concepts"][1]["code"] = "IT01 M2 10"
    report = normalize_intermediate(fixture, _strict_validation_fixture())
    signal = report["files"][0]["measurement_signals"][1]
    assert "M2" in signal["tokens"]
    assert signal["consolidated"] is False


def test_preserves_unknown_and_unsupported():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    bag = report["files"][0]["unknown_or_unsupported"]
    assert len(bag["unknown"]) == 1
    assert len(bag["unsupported"]) == 1


def test_preserves_manual_review():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    manual = report["files"][0]["manual_review"]
    assert any("MULTIPLE_UNITS_NON_BLOCKING" in item for item in manual)
    assert any("RELATION_ORPHAN_CHILD_NON_BLOCKING" in item for item in manual)


def test_preserves_source_trace():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    source = report["files"][0]["source_trace"]
    assert source["header_line"] == 1
    assert source["strict_traceability"]["lines_processed"] == 6


def test_generates_json_output():
    root = _make_root()
    try:
        report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
        json_path, _ = write_outputs(root, report)
        assert json_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "normalization_metadata" in loaded
    finally:
        _cleanup(root)


def test_generates_markdown_output():
    root = _make_root()
    try:
        report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
        _, md_path = write_outputs(root, report)
        assert md_path.exists()
        assert "BC3 Intermediate Normalization Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_no_master_import_contract():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    serialized = json.dumps(report)
    assert "master_import" not in serialized


def test_no_ratio_calculation_contract():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    serialized = json.dumps(report)
    assert '"ratios"' not in serialized
    assert '"ratio_calculation"' not in serialized


def test_no_final_consolidation_contract():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    serialized = json.dumps(report)
    assert "consolidated_amount" not in serialized


def test_no_final_category_normalization_contract():
    report = normalize_intermediate(_strict_parse_fixture(), _strict_validation_fixture())
    serialized = json.dumps(report)
    assert "final_normalized_categories" not in serialized


def test_does_not_modify_input():
    parse_fixture = _strict_parse_fixture()
    validation_fixture = _strict_validation_fixture()
    parse_before = json.dumps(parse_fixture, sort_keys=True)
    validation_before = json.dumps(validation_fixture, sort_keys=True)
    _ = normalize_intermediate(parse_fixture, validation_fixture)
    assert json.dumps(parse_fixture, sort_keys=True) == parse_before
    assert json.dumps(validation_fixture, sort_keys=True) == validation_before
