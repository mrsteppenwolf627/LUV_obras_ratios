from pathlib import Path
import shutil
import uuid

from scripts.inspect_samples import inspect_samples


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"inspect_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_inspect_samples_empty():
    root = _make_root()
    try:
        (root / "data" / "samples").mkdir(parents=True)

        inventory = inspect_samples(root)

        assert inventory["exists"] is True
        assert inventory["files_count"] == 0
        assert inventory["message"].startswith("No sample files")
    finally:
        _cleanup(root)


def test_inspect_samples_classification_and_hints():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)

        (samples / "presupuesto_final_v2.xls").write_text("not-real-excel", encoding="utf-8")
        (samples / "backup" / "mediciones.bc3").parent.mkdir(parents=True)
        (samples / "backup" / "mediciones.bc3").write_text("~K|sample", encoding="utf-8")
        (samples / "contrato.pdf").write_bytes(b"%PDF-1.4")

        inventory = inspect_samples(root)
        classes = {item["classification"] for item in inventory["files"]}

        assert inventory["files_count"] == 3
        assert {"EXCEL", "BC3", "PDF"}.issubset(classes)

        excel_entry = next(i for i in inventory["files"] if i["extension"] == ".xls")
        assert excel_entry["version_or_phase_hint"] is True

        bc3_entry = next(i for i in inventory["files"] if i["extension"] == ".bc3")
        assert bc3_entry["backup_hint"] is True

        pdf_entry = next(i for i in inventory["files"] if i["extension"] == ".pdf")
        assert pdf_entry["inspection"]["status"] == "REFERENCE_ONLY_DIAGNOSTIC"
    finally:
        _cleanup(root)

