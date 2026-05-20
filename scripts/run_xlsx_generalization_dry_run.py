#!/usr/bin/env python3
"""Phase 9.13 helper: run local XLSX dry-run generalization with sanitized IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.generate_live_excel_master import generate_preview_from_real_xlsx
    from scripts.live_excel_dry_run_evaluator import evaluate_dry_run_workbook
except ModuleNotFoundError:
    from generate_live_excel_master import generate_preview_from_real_xlsx  # type: ignore
    from live_excel_dry_run_evaluator import evaluate_dry_run_workbook  # type: ignore


ALLOWED_INPUT_ROOT = Path("data/samples")
ALLOWED_OUTPUT_ROOT = Path("outputs/live_excel_master/xlsx_generalization")
SANITIZED_IDS = [
    "REAL_XLSX_GENERALIZATION_001",
    "REAL_XLSX_GENERALIZATION_002",
    "REAL_XLSX_GENERALIZATION_003",
    "REAL_XLSX_GENERALIZATION_004",
    "REAL_XLSX_GENERALIZATION_005",
]


def _resolve_under(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _ensure_under(path: Path, allowed_root: Path, label: str) -> None:
    try:
        path.resolve().relative_to(allowed_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay under {allowed_root.as_posix()}") from exc


def run_xlsx_generalization_dry_run(
    files: list[Path],
    output_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    allowed_input = (repo_root / ALLOWED_INPUT_ROOT).resolve()
    allowed_output = (repo_root / ALLOWED_OUTPUT_ROOT).resolve()
    output_dir_abs = _resolve_under(repo_root, output_dir)
    _ensure_under(output_dir_abs, allowed_output, "output_dir")
    output_dir_abs.mkdir(parents=True, exist_ok=True)

    if not files:
        raise ValueError("At least one input XLSX file is required.")
    if len(files) > len(SANITIZED_IDS):
        raise ValueError(f"Maximum supported files for this phase: {len(SANITIZED_IDS)}")

    results: list[dict[str, Any]] = []
    for idx, file_arg in enumerate(files):
        run_id = SANITIZED_IDS[idx]
        input_abs = _resolve_under(repo_root, file_arg)
        _ensure_under(input_abs, allowed_input, "input file")
        if not input_abs.exists():
            raise RuntimeError(f"Input file does not exist: {file_arg}")
        if input_abs.suffix.lower() != ".xlsx":
            raise ValueError(f"Only .xlsx is allowed for phase 9.13 generalization: {file_arg}")

        preview_path = output_dir_abs / f"xlsx_generalization_{idx + 1:03d}_preview.xlsx"
        if preview_path.exists():
            preview_path.unlink()

        generate_preview_from_real_xlsx(
            input_xlsx_path=input_abs,
            output_path=preview_path,
            source_file_id=run_id,
        )
        evaluation = evaluate_dry_run_workbook(preview_path, run_id=run_id)
        results.append(
            {
                "run_id": run_id,
                "state": evaluation.state,
                "format": "XLSX",
                "reasons": evaluation.reasons,
                "metrics": evaluation.metrics,
                "preview_output": str(preview_path.as_posix()),
            }
        )

    return {
        "phase": "9.13",
        "auto_promotion_enabled": False,
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local XLSX dry-run generalization (phase 9.13).")
    parser.add_argument("--files", nargs="+", type=Path, required=True, help="Input XLSX files under data/samples.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ALLOWED_OUTPUT_ROOT,
        help="Output directory under outputs/live_excel_master/xlsx_generalization.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=ALLOWED_OUTPUT_ROOT / "xlsx_generalization_report_sanitized.json",
        help="Sanitized report path under outputs/live_excel_master/xlsx_generalization.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    allowed_output = (repo_root / ALLOWED_OUTPUT_ROOT).resolve()
    report_path = _resolve_under(repo_root, args.report_json)
    _ensure_under(report_path, allowed_output, "report_json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = run_xlsx_generalization_dry_run(files=args.files, output_dir=args.output_dir, repo_root=repo_root)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps({"report_json": str(report_path.as_posix()), "results": len(report["results"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
