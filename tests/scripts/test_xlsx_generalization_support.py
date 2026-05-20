from pathlib import Path
import shutil
import uuid

import pytest
from openpyxl import Workbook

from scripts.run_xlsx_generalization_dry_run import (
    ALLOWED_INPUT_ROOT,
    ALLOWED_OUTPUT_ROOT,
    SANITIZED_IDS,
    run_xlsx_generalization_dry_run,
)


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"xlsx_generalization_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _build_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Presupuesto"
    ws.append(["Codigo", "Descripcion", "Unidad", "Cantidad", "Precio Unitario", "Importe"])
    ws.append(["1", "Capitulo", "", "", "", ""])
    ws.append(["1.1.01", "Partida de prueba", "ud", 2, 50, 100])
    wb.save(path)
    wb.close()


def test_generalization_rejects_input_outside_allowed_zone():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        outside = root / "outside.xlsx"
        _build_xlsx(outside)
        with pytest.raises(ValueError, match="input file must stay under"):
            run_xlsx_generalization_dry_run(
                files=[outside],
                output_dir=ALLOWED_OUTPUT_ROOT,
                repo_root=root,
            )
    finally:
        _cleanup(root)


def test_generalization_rejects_non_xlsx_input():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        invalid = allowed_in / "sample.bc3"
        invalid.write_text("~V|FIEBDC-3/2020", encoding="utf-8")
        with pytest.raises(ValueError, match="Only .xlsx is allowed"):
            run_xlsx_generalization_dry_run(
                files=[Path("data/samples/sample.bc3")],
                output_dir=ALLOWED_OUTPUT_ROOT,
                repo_root=root,
            )
    finally:
        _cleanup(root)


def test_generalization_generates_sanitized_results_without_ratio_ingestion():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        file1 = allowed_in / "sample1.xlsx"
        file2 = allowed_in / "sample2.xlsx"
        _build_xlsx(file1)
        _build_xlsx(file2)

        report = run_xlsx_generalization_dry_run(
            files=[Path("data/samples/sample1.xlsx"), Path("data/samples/sample2.xlsx")],
            output_dir=ALLOWED_OUTPUT_ROOT,
            repo_root=root,
        )

        assert report["phase"] == "9.13"
        assert report["auto_promotion_enabled"] is False
        assert len(report["results"]) == 2
        assert report["results"][0]["run_id"] == SANITIZED_IDS[0]
        assert report["results"][1]["run_id"] == SANITIZED_IDS[1]
        for result in report["results"]:
            preview = Path(result["preview_output"])
            assert str((root / ALLOWED_OUTPUT_ROOT).resolve()) in str(preview.resolve())
            assert result["metrics"]["ratio_input_rows"] == 0.0
            assert result["metrics"]["ratio_calculated_rows"] == 0.0
    finally:
        _cleanup(root)


def test_generalization_limit_rejects_more_than_five_files():
    root = _make_root()
    try:
        allowed_in = root / ALLOWED_INPUT_ROOT
        allowed_in.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []
        for idx in range(6):
            path = allowed_in / f"sample{idx + 1}.xlsx"
            _build_xlsx(path)
            files.append(Path(f"data/samples/sample{idx + 1}.xlsx"))
        with pytest.raises(ValueError, match="Maximum supported files"):
            run_xlsx_generalization_dry_run(
                files=files,
                output_dir=ALLOWED_OUTPUT_ROOT,
                repo_root=root,
            )
    finally:
        _cleanup(root)
