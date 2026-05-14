from pathlib import Path
import json
import shutil
import uuid

from scripts.parse_bc3_preliminary import parse_bc3_file, parse_bc3_samples, write_outputs


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"parse_bc3_preliminary_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_parses_v_c_d_and_context_types():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        f = samples / "a.bc3"
        f.write_text(
            "~V|FIEBDC-3/2020\n"
            "~C|CAP01#\\Capitulo\n"
            "~D|CAP01#|IT01\n"
            "~K|IT01\\Partida|m2|12,00|120,00\n"
            "~M|IT01|medicion\n"
            "~T|IT01|texto\n",
            encoding="utf-8",
        )

        report = parse_bc3_samples(root)
        entry = report["files"][0]
        assert entry["header"]["has_v"] is True
        assert entry["records"]["record_type_counts"]["~C"] == 1
        assert len(entry["concepts"]) == 1
        assert len(entry["relations"]["links"]) == 1
        assert "~K" in entry["records"]["supported_record_types"]
        assert "~M" in entry["records"]["supported_record_types"]
        assert "~T" in entry["records"]["supported_record_types"]
    finally:
        _cleanup(root)


def test_unknown_records_are_preserved():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n~Z|foo|bar\n", encoding="utf-8")
        entry = parse_bc3_samples(root)["files"][0]
        assert "~Z" in entry["records"]["unknown_record_types"]
        assert any(r["record_type"] == "~Z" for r in entry["unsupported_records"])
    finally:
        _cleanup(root)


def test_report_contains_metadata_files_and_global_summary():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n", encoding="utf-8")
        report = parse_bc3_samples(root)
        assert "metadata" in report
        assert "files" in report
        assert "global_summary" in report
    finally:
        _cleanup(root)


def test_traceability_contains_line_numbers():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        p = samples / "a.bc3"
        p.write_text("~V|FIEBDC-3/2020\n~C|CAP01#\\Cap\n~D|CAP01#|IT01\n", encoding="utf-8")
        entry = parse_bc3_samples(root)["files"][0]
        assert entry["concepts"][0]["line_number"] == 2
        assert entry["relations"]["links"][0]["line_number"] == 3
        assert entry["raw_records"][0]["line_number"] >= 1
    finally:
        _cleanup(root)


def test_non_decodable_file_sets_errors():
    root = _make_root()
    try:
        f = root / "bad.bc3"
        f.write_bytes(b"\x81\x8d\x8f\x90\x9d")
        parsed = parse_bc3_file(f, root)
        assert "DECODE_FAILED" in parsed["risk_flags"]
        assert parsed["errors"]
    finally:
        _cleanup(root)


def test_missing_v_header_produces_error_and_manual_review():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~C|CAP01#\\Cap\n~D|CAP01#|IT01\n", encoding="utf-8")
        entry = parse_bc3_samples(root)["files"][0]
        assert "Missing ~V header." in entry["errors"]
        assert "MISSING_V_HEADER" in entry["manual_review_required"]
    finally:
        _cleanup(root)


def test_incomplete_relations_trigger_manual_review():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n~D|CAP01#|\n", encoding="utf-8")
        entry = parse_bc3_samples(root)["files"][0]
        assert "INCOMPLETE_RELATIONS_REVIEW" in entry["manual_review_required"]
    finally:
        _cleanup(root)


def test_json_and_markdown_outputs_generated():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n", encoding="utf-8")
        report = parse_bc3_samples(root)
        json_path, md_path = write_outputs(root, report)
        assert json_path.exists()
        assert md_path.exists()
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert "global_summary" in payload
        assert "BC3 Preliminary Parse Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_input_file_not_modified():
    root = _make_root()
    try:
        f = root / "immut.bc3"
        initial = b"~V|FIEBDC-3/2020\n~C|CAP01\\Title\n"
        f.write_bytes(initial)
        before = f.read_bytes()
        _ = parse_bc3_file(f, root)
        after = f.read_bytes()
        assert before == after
    finally:
        _cleanup(root)


def test_no_ratios_or_master_import_fields():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n", encoding="utf-8")
        report = parse_bc3_samples(root)
        for entry in report["files"]:
            assert "ratios" not in entry
            assert "master_import" not in entry
            assert "consolidated_amounts" not in entry
            assert "final_categories" not in entry
    finally:
        _cleanup(root)
