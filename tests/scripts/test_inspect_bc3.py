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
