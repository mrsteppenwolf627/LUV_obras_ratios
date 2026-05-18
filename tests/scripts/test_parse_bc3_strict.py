from pathlib import Path
import json
import shutil
import uuid

from scripts.parse_bc3_strict import parse_strict, parse_bc3_file_strict, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"parse_bc3_strict_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _mk_bc3(root: Path, rel: str, content: bytes) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)


def _base_reports() -> tuple[dict, dict]:
    parse_report = {
        "files": [
            {"file_ref": {"sanitized_id": "BC3_01", "relative_path": "data/samples/ok.bc3"}},
            {"file_ref": {"sanitized_id": "BC3_02", "relative_path": "data/samples/excluded.bc3"}},
        ]
    }
    validation_report = {
        "files": [
            {
                "sanitized_id": "BC3_01",
                "file_eligibility_status": "ELIGIBLE_FOR_PRELIMINARY_FLOW",
                "file_eligibility_reason": "OK",
            },
            {
                "sanitized_id": "BC3_02",
                "file_eligibility_status": "NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT",
                "file_eligibility_reason": "Decode failure",
            },
        ]
    }
    return parse_report, validation_report


def test_strict_parses_v_c_d():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|CAP01#\\Cap\n~D|CAP01#|IT01\n~C|IT01\\Item\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert entry["parsed"]["header"]["line_number"] == 1
        assert len(entry["parsed"]["concepts"]) == 2
        assert len(entry["parsed"]["relations"]) == 1
    finally:
        _cleanup(root)


def test_error_when_missing_v():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~C|CAP01#\\Cap\n~D|CAP01#|IT01\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert "MISSING_V_HEADER" in entry["errors"]
    finally:
        _cleanup(root)


def test_error_when_missing_concepts():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~D|A|B\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert "MISSING_C_CONCEPTS" in entry["errors"]
    finally:
        _cleanup(root)


def test_manual_review_partial_orphans():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~D|A#|X\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert any(i.startswith("PARTIAL_ORPHAN_RELATIONS:") for i in entry["manual_review_required"])
    finally:
        _cleanup(root)


def test_controlled_exclusion_for_not_eligible_file():
    root = _make_root()
    try:
        parse_report, validation_report = _base_reports()
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~C|B\\B\n~D|A#|B\n")
        _mk_bc3(root, "data/samples/excluded.bc3", b"bad")
        report = parse_strict(parse_report, validation_report, root)
        assert report["global_summary"]["excluded_files_count"] == 1
        assert report["controlled_exclusions"][0]["sanitized_id"] == "BC3_02"
    finally:
        _cleanup(root)


def test_valid_subset_can_advance_with_controlled_exclusions():
    root = _make_root()
    try:
        parse_report, validation_report = _base_reports()
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~C|B\\B\n~D|A#|B\n")
        _mk_bc3(root, "data/samples/excluded.bc3", b"bad")
        report = parse_strict(parse_report, validation_report, root)
        assert report["global_summary"]["valid_subset_status"] == "ADVANCE_ALLOWED"
    finally:
        _cleanup(root)


def test_full_corpus_blocked_with_structural_issue():
    root = _make_root()
    try:
        parse_report, validation_report = _base_reports()
        validation_report["files"][0]["file_eligibility_status"] = "BLOCKED_STRUCTURAL_ISSUE"
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n")
        report = parse_strict(parse_report, validation_report, root)
        assert report["global_summary"]["full_corpus_status"] == "BLOCKED"
    finally:
        _cleanup(root)


def test_unknown_and_unsupported_preserved():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~D|A#|B\n~K|foo\n~!|weird\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert len(entry["unsupported"]) >= 1
        assert len(entry["unknown"]) >= 1
    finally:
        _cleanup(root)


def test_traceability_by_line_and_record():
    root = _make_root()
    try:
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~C|B\\B\n~D|A#|B\n")
        entry = parse_bc3_file_strict(root / "data/samples/ok.bc3", root, "BC3_01", "data/samples/ok.bc3")
        assert entry["traceability"]["lines_processed"] == 4
        assert entry["traceability"]["parsed_records_count"] == 4
    finally:
        _cleanup(root)


def test_json_and_markdown_generated():
    root = _make_root()
    try:
        parse_report, validation_report = _base_reports()
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~C|B\\B\n~D|A#|B\n")
        _mk_bc3(root, "data/samples/excluded.bc3", b"bad")
        report = parse_strict(parse_report, validation_report, root)
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "global_summary" in loaded
        assert "BC3 Strict Parse Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_input_not_modified():
    root = _make_root()
    try:
        original = b"~V|FIEBDC-3/2020\n~C|A#\\A\n~D|A#|B\n"
        _mk_bc3(root, "data/samples/ok.bc3", original)
        p = root / "data/samples/ok.bc3"
        before = p.read_bytes()
        _ = parse_bc3_file_strict(p, root, "BC3_01", "data/samples/ok.bc3")
        assert p.read_bytes() == before
    finally:
        _cleanup(root)


def test_no_master_ratios_consolidation_or_normalization_fields():
    root = _make_root()
    try:
        parse_report, validation_report = _base_reports()
        _mk_bc3(root, "data/samples/ok.bc3", b"~V|FIEBDC-3/2020\n~C|A#\\A\n~C|B\\B\n~D|A#|B\n")
        _mk_bc3(root, "data/samples/excluded.bc3", b"bad")
        report = parse_strict(parse_report, validation_report, root)
        serialized = json.dumps(report)
        assert "master_import" not in serialized
        assert '"ratios"' not in serialized
        assert '"ratio_calculation"' not in serialized
        assert "consolidated_amount" not in serialized
        assert "final_normalized_categories" not in serialized
    finally:
        _cleanup(root)
