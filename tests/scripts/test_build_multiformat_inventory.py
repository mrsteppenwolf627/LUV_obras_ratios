from pathlib import Path
import json
import shutil
import uuid

from scripts.build_multiformat_inventory import build_multiformat_inventory, write_reports


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"build_multiformat_inventory_{uuid.uuid4().hex}"
    (root / "data" / "samples").mkdir(parents=True)
    (root / "reports" / "excel_full_reader").mkdir(parents=True)
    (root / "reports" / "presto_diagnostics").mkdir(parents=True)
    (root / "reports" / "bc3_strict_parse").mkdir(parents=True)
    (root / "reports" / "bc3_strict_validation").mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _write_reports(root: Path) -> None:
    (root / "reports" / "excel_full_reader" / "excel_full_reader_inventory.json").write_text(
        json.dumps(
            {
                "workbook_summaries": [
                    {
                        "workbook_ref": "data/samples/book.xlsx",
                        "relative_path_sanitized": "data/samples/book.xlsx",
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
                "sheets": [],
                "global_summary": {"traced_cells_total": 0},
                "controlled_exclusions": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "reports" / "bc3_strict_parse" / "bc3_strict_parse_inventory.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "file_ref": {"sanitized_id": "BC3_01", "relative_path": "data/samples/book.bc3"},
                        "parsed": {"header": {"line_number": 1}, "concepts": [], "relations": []},
                        "unknown": [],
                        "unsupported": [],
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "reports" / "bc3_strict_validation" / "bc3_strict_validation_report.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "sanitized_id": "BC3_01",
                        "relative_path": "data/samples/book.bc3",
                        "validation_readiness": "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW",
                        "errors": [],
                        "manual_review_items": [],
                    }
                ],
                "validation_readiness": {"global": "VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW"},
                "global_validation_summary": {"full_corpus_status": "NOT_BLOCKED"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "reports" / "presto_diagnostics" / "presto_diagnostics_inventory.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "relative_path_sanitized": "data/samples/raw.Presto",
                        "support_classification": "NEEDS_VENDOR_EXPORT",
                        "parser_or_reader_used": "none",
                        "internal_names_sample": [],
                        "notes": "Proprietary container",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_builds_common_inventory_across_formats():
    root = _make_root()
    try:
        (root / "data" / "samples" / "book.xlsx").write_bytes(b"x")
        (root / "data" / "samples" / "book.bc3").write_bytes(b"y")
        (root / "data" / "samples" / "raw.Presto").write_bytes(b"z")
        (root / "data" / "samples" / "note.txt").write_text("note", encoding="utf-8")
        _write_reports(root)

        payload = build_multiformat_inventory(root)
        by_path = {item["file_ref"]["relative_path_sanitized"]: item for item in payload["files"]}

        assert payload["global_summary"]["files_total"] == 4
        assert by_path["data/samples/book.xlsx"]["format_type"] == "EXCEL"
        assert by_path["data/samples/book.xlsx"]["parser_or_reader_used"] == "read_excel_full"
        assert by_path["data/samples/book.bc3"]["format_type"] == "BC3"
        assert by_path["data/samples/book.bc3"]["eligibility_status"] == "ELIGIBLE_WITH_NON_BLOCKING_MANUAL_REVIEW"
        assert by_path["data/samples/raw.Presto"]["format_type"] == "PRESTO"
        assert by_path["data/samples/raw.Presto"]["eligibility_status"] == "NEEDS_VENDOR_EXPORT"
        assert by_path["data/samples/note.txt"]["eligibility_status"] == "NOT_IN_SCOPE"
        assert payload["controlled_exclusions"]
    finally:
        _cleanup(root)


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        (root / "data" / "samples" / "book.xlsx").write_bytes(b"x")
        _write_reports(root)
        payload = build_multiformat_inventory(root)
        json_path, md_path = write_reports(root, payload)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "inventory_metadata" in loaded
        assert "Multiformat Inventory Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_input_not_modified():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "book.xlsx"
        file_path.write_bytes(b"x")
        _write_reports(root)
        before = file_path.read_bytes()
        _ = build_multiformat_inventory(root)
        after = file_path.read_bytes()
        assert before == after
    finally:
        _cleanup(root)

