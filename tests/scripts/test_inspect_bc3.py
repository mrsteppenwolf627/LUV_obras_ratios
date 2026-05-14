from pathlib import Path
import json
import shutil
import uuid

from scripts.inspect_bc3 import inspect_bc3_file, inspect_bc3_samples, write_reports


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"inspect_bc3_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_minimal_bc3_header_and_counts():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        bc3 = samples / "mini.bc3"
        bc3.write_text(
            "~V|FIEBDC-3/2020\n~C|CAP01\\Capitulo 1\n~D|CAP01|PAR01\n~K|PAR01\\Partida 1|m2|10,00|100,00\n",
            encoding="cp1252",
        )

        report = inspect_bc3_samples(root)
        assert report["bc3_files_count"] == 1
        insp = report["files"][0]["inspection"]
        assert insp["status"] == "BC3_DIAGNOSTIC_OK"
        assert insp["record_type_counts"]["~V"] == 1
        assert insp["record_type_counts"]["~C"] == 1
        assert insp["record_type_counts"]["~D"] == 1
        assert insp["record_type_counts"]["~K"] == 1
        assert "CAP01" in insp["chapter_code_candidates"]
        assert insp["hierarchy_relations_candidates"][0]["parent"] == "CAP01"
        assert insp["hierarchy_relations_candidates"][0]["child"] == "PAR01"
        assert "m2" in insp["units_detected"]
        assert insp["c_code_classification"]["chapter_candidates_count"] >= 1
        assert "~C" in insp["record_type_stats"]
        assert insp["record_type_stats"]["~C"]["count"] == 1

    finally:
        _cleanup(root)


def test_cp1252_detection():
    root = _make_root()
    try:
        bc3 = root / "cp1252.bc3"
        bc3.write_bytes("~V|FIEBDC-3/2020|Descripci\xf3n\n".encode("latin-1"))
        insp = inspect_bc3_file(bc3)
        assert insp["status"] == "BC3_DIAGNOSTIC_OK"
        assert insp["encoding"] == "cp1252"
    finally:
        _cleanup(root)


def test_reports_json_and_markdown_generated():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n", encoding="utf-8")

        report = inspect_bc3_samples(root)
        json_path, md_path = write_reports(root, report)
        assert json_path.exists()
        assert md_path.exists()
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["bc3_files_count"] == 1
        assert "variant_warnings" in payload
        assert "readiness_summary" in payload
        assert "readiness_blockers" in payload["readiness_summary"]
        assert "readiness_non_blocking_warnings" in payload["readiness_summary"]
        assert "manual_review_reasons" in payload["readiness_summary"]
        assert "phase_4_recommendation" in payload["readiness_summary"]
        assert "bc3_comparison" in payload
        assert "sensitivity" in payload
        assert "BC3 Diagnostic Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_empty_file_safe_behavior():
    root = _make_root()
    try:
        bc3 = root / "empty.bc3"
        bc3.write_bytes(b"")
        insp = inspect_bc3_file(bc3)
        assert insp["status"] == "BC3_DIAGNOSTIC_OK"
        assert insp["encoding"] == "unknown"
        assert insp["record_type_counts"] == {}
    finally:
        _cleanup(root)


def test_non_utf8_bytes_safe_behavior():
    root = _make_root()
    try:
        bc3 = root / "bytes.bc3"
        bc3.write_bytes(b"~V|FIEBDC-3/2020|\x96\x97\x93\n")
        insp = inspect_bc3_file(bc3)
        assert insp["status"] == "BC3_DIAGNOSTIC_OK"
        assert insp["encoding"] in {"cp1252", "utf-8"}
    finally:
        _cleanup(root)


def test_input_file_not_modified():
    root = _make_root()
    try:
        bc3 = root / "immut.bc3"
        initial = b"~V|FIEBDC-3/2020\n~C|CAP01\\Titulo\n"
        bc3.write_bytes(initial)
        before = bc3.read_bytes()
        _ = inspect_bc3_file(bc3)
        after = bc3.read_bytes()
        assert before == after
    finally:
        _cleanup(root)


def test_c_code_classification_chapter_item_other():
    root = _make_root()
    try:
        bc3 = root / "codes.bc3"
        bc3.write_text(
            "~V|FIEBDC-3/2020\n"
            "~C|CAP01#\\Capitulo\n"
            "~C|CAP0101\\Partida\n"
            "~C|X_MISC\\Otro\n",
            encoding="utf-8",
        )
        insp = inspect_bc3_file(bc3)
        cls = insp["c_code_classification"]
        assert cls["chapter_candidates_count"] == 1
        assert cls["item_candidates_count"] == 1
        assert cls["other_candidates_count"] == 1
    finally:
        _cleanup(root)


def test_hierarchy_depth_and_incomplete_relations_warning():
    root = _make_root()
    try:
        bc3 = root / "hier.bc3"
        bc3.write_text(
            "~V|FIEBDC-3/2020\n"
            "~D|A#|B1\n"
            "~D|B1|C1\n"
            "~D|C1|\n",
            encoding="utf-8",
        )
        insp = inspect_bc3_file(bc3)
        hs = insp["hierarchy_summary"]
        assert hs["max_depth_approx"] >= 2
        assert hs["incomplete_relations_count"] == 1
        assert any(w.startswith("INCOMPLETE_RELATIONS:") for w in insp["warnings"])
    finally:
        _cleanup(root)


def test_economic_and_text_diagnostics_and_unknown_record_warning():
    root = _make_root()
    try:
        bc3 = root / "diag.bc3"
        bc3.write_text(
            "~V|FIEBDC-3/2020\n"
            "~Z|foo|bar\n"
            "~K|IT01\\Descripcion de prueba muy larga para diagnostico textual|m2|10,00|100,00\n",
            encoding="utf-8",
        )
        insp = inspect_bc3_file(bc3)
        eco = insp["economic_field_diagnostics"]
        txt = insp["text_field_diagnostics"]
        assert eco["numeric_tokens_by_record_type"]["~K"] >= 1
        assert isinstance(eco["ambiguous_economic_tokens"], bool)
        assert "~K" in txt["most_textual_record_types"]
        assert any(w.startswith("NON_COMMON_RECORD_TYPES:") for w in insp["warnings"])
    finally:
        _cleanup(root)


def test_markdown_contains_new_heuristics_summary():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text(
            "~V|FIEBDC-3/2020\n~C|CAP01#\\Capitulo\n~D|CAP01#|ITEM01\n~K|ITEM01\\Desc larga larga larga larga larga|m2|1,00|2,00\n",
            encoding="utf-8",
        )
        report = inspect_bc3_samples(root)
        _, md_path = write_reports(root, report)
        md = md_path.read_text(encoding="utf-8")
        assert "C code classes:" in md
        assert "Hierarchy summary:" in md
        assert "Text diagnostics:" in md
        assert "## Global Readiness" in md
        assert "## BC3 Comparison" in md
        assert "Readiness blockers:" in md
        assert "Phase 4 recommendation:" in md
    finally:
        _cleanup(root)


def test_sanitizes_absolute_path_and_truncates_long_text():
    root = _make_root()
    try:
        bc3 = root / "sanitize.bc3"
        long_text = "A" * 220
        bc3.write_text(
            "~V|FIEBDC-3/2020|C:\\\\sensitive\\\\path\\\\file\n"
            f"~K|IT01\\{long_text}|m2|1,00|2,00\n",
            encoding="utf-8",
        )
        insp = inspect_bc3_file(bc3)
        samples = insp["record_type_stats"]["~V"]["samples_sanitized"]
        assert all("C:\\sensitive" not in s for s in samples)
        assert all(len(s) <= 80 for s in samples)
    finally:
        _cleanup(root)


def test_report_marks_potentially_sensitive_data():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n~K|I\\D|m2|1,00|2,00\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        assert report["sensitivity"]["contains_potentially_sensitive_data"] is True
    finally:
        _cleanup(root)


def test_blocked_risk_for_non_decodable_file():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "bad.bc3").write_bytes(b"\x81\x8d\x8f\x90\x9d")
        report = inspect_bc3_samples(root)
        risks = report["files"][0]["risk_matrix"]
        assert any(r["severity"] == "BLOCKED" for r in risks)
    finally:
        _cleanup(root)


def test_missing_v_header_raises_error_risk():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "nov.bc3").write_text("~C|CAP01#\\Cap\n~D|CAP01#|ITEM1\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        risks = report["files"][0]["risk_matrix"]
        assert any(r["severity"] in {"ERROR", "BLOCKED"} and r["code"] == "MISSING_V_HEADER" for r in risks)
    finally:
        _cleanup(root)


def test_readiness_ready_for_preliminary_design():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "clean.bc3").write_text("~V|FIEBDC-3/2020\n~C|AB12#\\Cap\n~D|AB12#|AB1201\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        assert report["readiness_summary"]["status"] == "READY_FOR_PRELIMINARY_PARSER_DESIGN"
        assert report["readiness_summary"]["readiness_blockers"] == []
    finally:
        _cleanup(root)


def test_readiness_needs_more_heuristics_on_structural_warning():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "warn.bc3").write_text("~V|FIEBDC-3/2020\n~D|ROOT|\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        assert report["readiness_summary"]["status"] == "NEEDS_MORE_DIAGNOSTIC_HEURISTICS"
        assert "INCOMPLETE_RELATIONS" in report["readiness_summary"]["readiness_blockers"]
        assert "INCOMPLETE_RELATIONS" in report["readiness_summary"]["manual_review_reasons"]
    finally:
        _cleanup(root)


def test_readiness_blocked_on_decode():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "blocked.bc3").write_bytes(b"\x81\x8d\x8f\x90\x9d")
        report = inspect_bc3_samples(root)
        assert report["readiness_summary"]["status"] == "BLOCKED_BY_DECODING_OR_STRUCTURE"
    finally:
        _cleanup(root)


def test_comparison_between_two_bc3_with_distinct_record_types():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n~C|AB12#\\Cap\n~G|X\n", encoding="utf-8")
        (samples / "b.bc3").write_text("~V|FIEBDC-3/2020\n~C|CD34#\\Cap\n~L|Y\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        comp = report["bc3_comparison"]
        assert len(comp["files_considered"]) == 2
        assert "~V" in comp["record_types_common_to_all"]
        assert any(comp["record_types_exclusive_by_file"][sid] for sid in comp["files_considered"])
    finally:
        _cleanup(root)


def test_variant_difference_is_non_blocking_warning():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / "a.bc3").write_text("~V|FIEBDC-3/2020\n~C|AB12#\\Cap\n~G|X\n", encoding="utf-8")
        (samples / "b.bc3").write_text("~V|FIEBDC-3/2002\n~C|CD34#\\Cap\n", encoding="utf-8")
        report = inspect_bc3_samples(root)
        rd = report["readiness_summary"]
        assert "VARIANT_RECORD_TYPES_DIFFERENCE" in rd["readiness_non_blocking_warnings"]
        assert "VARIANT_RECORD_TYPES_DIFFERENCE" not in rd["readiness_blockers"]
        assert rd["status"] == "READY_FOR_PRELIMINARY_PARSER_DESIGN"
    finally:
        _cleanup(root)
