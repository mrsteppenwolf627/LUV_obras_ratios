from pathlib import Path
import shutil
import uuid

import pytest
from openpyxl import Workbook

from scripts.run_real_dry_run_pilot import (
    ALLOWED_INPUT_ROOT,
    ALLOWED_OUTPUT_ROOT,
    run_real_dry_run_pilot,
)


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"live_master_real_dry_run_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _build_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Presupuesto"
    ws.append(["Codigo", "Descripcion", "Importe"])
    ws.append(["1.1", "Partida de prueba", 100])
    wb.save(path)
    wb.close()


def test_wrapper_rejects_input_outside_allowed_zone():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        outside = root / "outside.xlsx"
        _build_xlsx(outside)
        with pytest.raises(ValueError, match="input file must stay under"):
            run_real_dry_run_pilot(files=[outside], output_dir=ALLOWED_OUTPUT_ROOT, repo_root=root)
    finally:
        _cleanup(root)


def test_wrapper_generates_sanitized_results_for_xlsx_and_bc3():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        file1 = allowed_in / "sample1.xlsx"
        file2 = allowed_in / "sample2.bc3"
        _build_xlsx(file1)
        file2.write_text("~V|FIEBDC-3/2020", encoding="utf-8")

        report = run_real_dry_run_pilot(
            files=[Path("data/samples/sample1.xlsx"), Path("data/samples/sample2.bc3")],
            output_dir=ALLOWED_OUTPUT_ROOT,
            repo_root=root,
        )

        assert report["auto_promotion_enabled"] is False
        assert len(report["results"]) == 2
        assert report["results"][0]["run_id"] == "REAL_DRY_RUN_001"
        assert report["results"][1]["run_id"] == "REAL_DRY_RUN_002"
        assert report["results"][1]["state"] == "PROMOTION_BLOCKED"
        assert "format_not_supported_for_preview_phase_9_10" in report["results"][1]["reasons"]
    finally:
        _cleanup(root)


def test_wrapper_does_not_write_ratio_sheets_and_uses_allowed_output_root():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        file1 = allowed_in / "sample3.xlsx"
        _build_xlsx(file1)

        report = run_real_dry_run_pilot(
            files=[Path("data/samples/sample3.xlsx")],
            output_dir=ALLOWED_OUTPUT_ROOT,
            repo_root=root,
        )
        result = report["results"][0]
        preview = Path(result["preview_output"])
        assert str((root / ALLOWED_OUTPUT_ROOT).resolve()) in str(preview.resolve())
        assert result["metrics"]["ratio_input_rows"] == 0.0
        assert result["metrics"]["ratio_calculated_rows"] == 0.0
    finally:
        _cleanup(root)
