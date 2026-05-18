from pathlib import Path
import json
import shutil
import uuid

from scripts.validate_bc3_strict import validate_strict, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"validate_bc3_strict_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _base_strict_report() -> dict:
    return {
        "metadata": {"generated_at": "2026-01-01T00:00:00+00:00", "parser_stage": "strict"},
        "files": [
            {
                "file_ref": {"sanitized_id": "BC3_01", "relative_path": "data/samples/a.bc3"},
                "parsed": {
                    "header": {"line_number": 1, "raw": "~V|FIEBDC-3/2020"},
                    "concepts": [
                        {"line_number": 2, "record_type": "~C", "code": "A#"},
                        {"line_number": 3, "record_type": "~C", "code": "B"},
                    ],
                    "relations": [
                        {"line_number": 4, "record_type": "~D", "parent_code": "A#", "child_code": "B"}
                    ],
                },
                "unknown": [{"line_number": 5, "raw": "~!|x", "reason": "malformed"}],
                "unsupported": [{"line_number": 6, "record_type": "~K", "raw": "~K|x"}],
                "errors": [],
                "warnings": [],
                "manual_review_required": [],
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


def test_valid_strict_json():
    report = validate_strict(_base_strict_report(), "strict.json")
    assert report["validation_metadata"]["status"] in {"VALID", "MANUAL_REVIEW_REQUIRED"}


def test_missing_metadata_blocks():
    payload = _base_strict_report()
    payload.pop("metadata")
    report = validate_strict(payload, "strict.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_missing_files_blocks():
    payload = _base_strict_report()
    payload.pop("files")
    report = validate_strict(payload, "strict.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_missing_global_summary_blocks():
    payload = _base_strict_report()
    payload.pop("global_summary")
    report = validate_strict(payload, "strict.json")
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_valid_relation_against_existing_concepts():
    report = validate_strict(_base_strict_report(), "strict.json")
    assert not any(item["code"] == "ORPHAN_RELATIONS_BLOCKING" for item in report["blocking_errors"])


def test_code_hash_equivalence():
    payload = _base_strict_report()
    payload["files"][0]["parsed"]["relations"] = [
        {"line_number": 4, "record_type": "~D", "parent_code": "A", "child_code": "B#"}
    ]
    report = validate_strict(payload, "strict.json")
    assert not report["blocking_errors"]


def test_partial_orphan_is_manual_review():
    payload = _base_strict_report()
    payload["files"][0]["parsed"]["relations"] = [
        {"line_number": 4, "record_type": "~D", "parent_code": "A#", "child_code": "MISS"}
    ]
    report = validate_strict(payload, "strict.json")
    assert any(item["code"] == "RELATION_ORPHAN_CHILD_NON_BLOCKING" for item in report["manual_review_items"])


def test_massive_orphan_blocks():
    payload = _base_strict_report()
    payload["files"][0]["parsed"]["relations"] = [
        {"line_number": i + 1, "record_type": "~D", "parent_code": "A#", "child_code": f"MISS{i}"}
        for i in range(20)
    ]
    report = validate_strict(payload, "strict.json")
    assert any(item["code"] == "ORPHAN_RELATIONS_BLOCKING" for item in report["blocking_errors"])
    assert report["validation_readiness"]["global"] == "VALIDATION_BLOCKED"


def test_excluded_file_does_not_block_valid_subset():
    report = validate_strict(_base_strict_report(), "strict.json")
    summary = report["global_validation_summary"]
    assert summary["excluded_files_count"] == 1
    assert summary["valid_subset_status"] == "ADVANCE_ALLOWED"


def test_unknown_and_unsupported_preserved_counts():
    report = validate_strict(_base_strict_report(), "strict.json")
    file_report = report["files"][0]
    assert file_report["unknown_preserved_count"] == 1
    assert file_report["unsupported_preserved_count"] == 1


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        report = validate_strict(_base_strict_report(), "strict.json")
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "global_validation_summary" in loaded
        assert "BC3 Strict Validation Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_no_master_or_ratios_or_consolidation_or_normalization():
    report = validate_strict(_base_strict_report(), "strict.json")
    serialized = json.dumps(report)
    assert "master_import" not in serialized
    assert '"ratios"' not in serialized
    assert '"ratio_calculation"' not in serialized
    assert "consolidated_amount" not in serialized
    assert "final_normalized_categories" not in serialized
