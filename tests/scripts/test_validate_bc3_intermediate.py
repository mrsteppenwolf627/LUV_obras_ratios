from pathlib import Path
import json
import shutil
import uuid

from scripts.validate_bc3_intermediate import validate_intermediate, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"validate_bc3_intermediate_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _base_file_entry() -> dict:
    return {
        "file_ref": {"sanitized_id": "BC3_01", "relative_path": "data/samples/a.bc3"},
        "decode": {"encoding": "utf-8", "confidence": "high", "strategy": "utf-8"},
        "header": {"has_v": True, "v_line_number": 1, "fiebdc_version_candidate": "FIEBDC-3/2020"},
        "records": {"unknown_record_types": [], "record_type_counts": {"~V": 1, "~C": 1, "~D": 1}},
        "concepts": [{"line_number": 2, "record_type": "~C", "code": "CAP01#"}],
        "relations": {"links": [{"line_number": 3, "parent_code": "CAP01#", "child_code": "CAP01#"}]},
        "units": ["m2"],
        "risk_flags": ["PRELIMINARY_PARSE_OK"],
        "errors": [],
        "warnings": [],
        "manual_review_required": [],
    }


def _valid_intermediate() -> dict:
    return {
        "metadata": {"generated_at": "2026-01-01T00:00:00+00:00"},
        "files": [_base_file_entry()],
        "global_summary": {"bc3_files_count": 1},
    }


def test_valid_intermediate_json():
    report = validate_intermediate(_valid_intermediate(), "synthetic.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN"
    assert report["global_validation_summary"]["files_count"] == 1


def test_missing_metadata_blocks():
    payload = _valid_intermediate()
    payload.pop("metadata")
    report = validate_intermediate(payload, "synthetic.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_missing_files_blocks():
    payload = _valid_intermediate()
    payload.pop("files")
    report = validate_intermediate(payload, "synthetic.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_missing_v_header_is_error():
    payload = _valid_intermediate()
    payload["files"][0]["header"]["has_v"] = False
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "MISSING_V_HEADER" for item in report["blocking_items"])
    assert report["validation_readiness"]["files"][0]["readiness"] == "VALIDATION_BLOCKED"


def test_missing_concepts_flags_warning_and_manual_review():
    payload = _valid_intermediate()
    payload["files"][0]["concepts"] = []
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "MISSING_C_CONCEPTS" for item in report["warnings"])
    assert any(item["code"] == "CONCEPTS_ABSENT_REVIEW" for item in report["blocking_items"])


def test_relation_with_missing_parent():
    payload = _valid_intermediate()
    payload["files"][0]["relations"]["links"] = [{"line_number": 3, "parent_code": "P1", "child_code": "CAP01#"}]
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "RELATION_PARENT_NOT_IN_CONCEPTS" for item in report["warnings"])
    assert any(item["code"] == "RELATION_ORPHAN_CHILD_NON_BLOCKING" for item in report["non_blocking_manual_review_items"])


def test_relation_with_missing_child():
    payload = _valid_intermediate()
    payload["files"][0]["relations"]["links"] = [{"line_number": 3, "parent_code": "CAP01#", "child_code": "C2"}]
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "RELATION_CHILD_NOT_IN_CONCEPTS" for item in report["warnings"])


def test_unknown_records_under_threshold_is_warning():
    payload = _valid_intermediate()
    payload["files"][0]["records"]["unknown_record_types"] = ["~Z"]
    report = validate_intermediate(payload, "synthetic.json", unknown_threshold=2)
    assert any(item["code"] == "UNKNOWN_RECORDS_UNDER_THRESHOLD" for item in report["non_blocking_manual_review_items"])


def test_unknown_records_over_threshold_non_predominant_is_non_blocking():
    payload = _valid_intermediate()
    payload["files"][0]["records"]["unknown_record_types"] = ["~Z", "~Y", "~X"]
    payload["files"][0]["records"]["record_type_counts"].update({"~Z": 1, "~Y": 1, "~X": 1, "~C": 100})
    report = validate_intermediate(payload, "synthetic.json", unknown_threshold=2)
    assert any(item["code"] == "UNKNOWN_RECORDS_OVER_THRESHOLD" for item in report["non_blocking_manual_review_items"])


def test_manual_review_without_explicit_reason():
    payload = _valid_intermediate()
    payload["files"][0]["concepts"] = []
    payload["files"][0]["manual_review_required"] = []
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "MISSING_MANUAL_REASONS" for item in report["minor_adjustment_items"])


def test_separation_errors_warnings_manual_review():
    payload = _valid_intermediate()
    payload["files"][0]["header"]["has_v"] = False
    payload["files"][0]["records"]["unknown_record_types"] = ["~Z"]
    report = validate_intermediate(payload, "synthetic.json", unknown_threshold=2)
    assert report["blocking_items"]
    assert report["non_blocking_manual_review_items"] is not None


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        report = validate_intermediate(_valid_intermediate(), "synthetic.json")
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "global_validation_summary" in loaded
        assert "validation_readiness" in loaded
        md = md_path.read_text(encoding="utf-8")
        assert "BC3 Intermediate Validation Report" in md
        assert "## Readiness" in md
    finally:
        _cleanup(root)


def test_input_not_modified():
    payload = _valid_intermediate()
    before = json.dumps(payload, sort_keys=True)
    _ = validate_intermediate(payload, "synthetic.json")
    after = json.dumps(payload, sort_keys=True)
    assert before == after


def test_no_ratio_or_master_import_fields_in_validation():
    report = validate_intermediate(_valid_intermediate(), "synthetic.json")
    serialized = json.dumps(report)
    assert "master_import" not in serialized
    assert "ratio_calculation" not in serialized


def test_manual_review_non_blocking_multiple_units():
    payload = _valid_intermediate()
    payload["files"][0]["units"] = ["m2", "m3"]
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "MULTIPLE_UNITS_NON_BLOCKING" for item in report["non_blocking_manual_review_items"])


def test_future_human_decision_units_and_economic():
    payload = _valid_intermediate()
    payload["files"][0]["units"] = ["m2", "m3"]
    payload["files"][0]["economic_signals"] = {"ambiguous_economic_tokens": True}
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "UNITS_POLICY_PENDING" for item in report["future_human_decisions"])
    assert any(item["code"] == "ECONOMIC_POLICY_PENDING" for item in report["future_human_decisions"])


def test_readiness_ready_with_non_blocking_manual_review():
    payload = _valid_intermediate()
    payload["files"][0]["records"]["unknown_record_types"] = ["~Z"]
    payload["files"][0]["manual_review_required"] = ["UNKNOWN_TYPES_TRACKED"]
    report = validate_intermediate(payload, "synthetic.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW"


def test_readiness_needs_minor_adjustments_on_unclassified_warning():
    payload = _valid_intermediate()
    payload["files"][0]["warnings"] = ["SOME_NEW_WARNING"]
    report = validate_intermediate(payload, "synthetic.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_NEEDS_MINOR_ADJUSTMENTS"


def test_unknown_records_predominant_blocks():
    payload = _valid_intermediate()
    payload["files"][0]["records"]["unknown_record_types"] = ["~Z", "~Y", "~X"]
    payload["files"][0]["records"]["record_type_counts"] = {"~V": 1, "~C": 1, "~D": 1, "~Z": 40, "~Y": 30, "~X": 20}
    report = validate_intermediate(payload, "synthetic.json", unknown_threshold=2)
    assert any(item["code"] == "UNKNOWN_RECORDS_PREDOMINANT" for item in report["blocking_items"])


def test_orphan_relations_limited_non_blocking():
    payload = _valid_intermediate()
    payload["files"][0]["relations"]["links"] = [
        {"line_number": 3, "parent_code": "CAP01#", "child_code": "X1"},
        {"line_number": 4, "parent_code": "CAP01#", "child_code": "X2"},
        {"line_number": 5, "parent_code": "CAP01#", "child_code": "CAP01#"},
    ]
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "RELATION_ORPHAN_CHILD_NON_BLOCKING" for item in report["non_blocking_manual_review_items"])


def test_orphan_relations_massive_blocks():
    payload = _valid_intermediate()
    payload["files"][0]["concepts"] = [{"line_number": 1, "record_type": "~C", "code": "CAP01#"}]
    payload["files"][0]["relations"]["links"] = [
        {"line_number": i + 1, "parent_code": "CAP01#", "child_code": f"MISS{i}"} for i in range(20)
    ]
    report = validate_intermediate(payload, "synthetic.json")
    assert any(item["code"] == "ORPHAN_RELATIONS_BLOCKING" for item in report["blocking_items"])
