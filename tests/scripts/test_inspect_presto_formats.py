from pathlib import Path
import json
import shutil
import sqlite3
import uuid
import zipfile

from scripts.inspect_presto_formats import inspect_presto_formats, write_reports


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"inspect_presto_formats_{uuid.uuid4().hex}"
    (root / "data" / "samples").mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_zip_container_classified_with_standard_library():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "work.Presto"
        with zipfile.ZipFile(file_path, "w") as zf:
            zf.writestr("inside.txt", "hola")

        payload = inspect_presto_formats(root)
        item = next(item for item in payload["files"] if item["relative_path_sanitized"] == "data/samples/work.Presto")
        assert item["support_classification"] == "READABLE_WITH_STANDARD_LIBRARY"
        assert item["parser_or_reader_used"] == "zipfile"
        assert item["internal_names_sample"] == ["inside.txt"]
    finally:
        _cleanup(root)


def test_sqlite_container_classified_with_standard_library():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "work.pzh"
        conn = sqlite3.connect(file_path)
        try:
            conn.execute("CREATE TABLE demo(id INTEGER)")
            conn.commit()
        finally:
            conn.close()

        payload = inspect_presto_formats(root)
        item = next(item for item in payload["files"] if item["relative_path_sanitized"] == "data/samples/work.pzh")
        assert item["support_classification"] == "READABLE_WITH_STANDARD_LIBRARY"
        assert item["parser_or_reader_used"] == "sqlite3"
        assert item["internal_names_sample"]
    finally:
        _cleanup(root)


def test_text_like_presto_file_classified_directly_readable():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "record.PrestoRecord"
        file_path.write_text("PRESTO\nLINE 1\nLINE 2", encoding="utf-8")

        payload = inspect_presto_formats(root)
        item = next(item for item in payload["files"] if item["relative_path_sanitized"] == "data/samples/record.PrestoRecord")
        assert item["support_classification"] == "DIRECTLY_READABLE"
        assert item["parser_or_reader_used"] == "text_decoder"
    finally:
        _cleanup(root)


def test_binary_presto_like_file_needs_vendor_export():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "backup.PrestoBackup"
        file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")

        payload = inspect_presto_formats(root)
        item = next(item for item in payload["files"] if item["relative_path_sanitized"] == "data/samples/backup.PrestoBackup")
        assert item["support_classification"] == "NEEDS_VENDOR_EXPORT"
        assert item["parser_or_reader_used"] == "none"
        assert payload["manual_review"]
    finally:
        _cleanup(root)


def test_non_presto_files_are_controlled_exclusions():
    root = _make_root()
    try:
        (root / "data" / "samples" / "note.txt").write_text("x", encoding="utf-8")

        payload = inspect_presto_formats(root)
        assert payload["global_summary"]["presto_like_files_total"] == 0
        assert payload["controlled_exclusions"]
    finally:
        _cleanup(root)


def test_json_and_markdown_generation():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "work.Presto"
        with zipfile.ZipFile(file_path, "w") as zf:
            zf.writestr("inside.txt", "hola")

        payload = inspect_presto_formats(root)
        json_path, md_path = write_reports(root, payload)
        assert json_path.exists()
        assert md_path.exists()
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert "diagnostics_metadata" in loaded
        assert "Presto Diagnostics Report" in md_path.read_text(encoding="utf-8")
    finally:
        _cleanup(root)


def test_does_not_modify_input_file():
    root = _make_root()
    try:
        file_path = root / "data" / "samples" / "work.Presto"
        file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        before = file_path.read_bytes()

        _ = inspect_presto_formats(root)
        after = file_path.read_bytes()

        assert before == after
    finally:
        _cleanup(root)

