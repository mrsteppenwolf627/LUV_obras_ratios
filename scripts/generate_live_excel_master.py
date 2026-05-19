#!/usr/bin/env python3
"""Create or update a controlled live Excel master template."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
from typing import Iterable

from openpyxl import Workbook, load_workbook  # type: ignore

DEFAULT_OUTPUT = Path("outputs/live_excel_master/live_excel_master.xlsx")
ALLOWED_OUTPUT_ROOT = Path("outputs/live_excel_master")
SNAPSHOTS_DIRNAME = "snapshots"

REQUIRED_SHEETS_COLUMNS: dict[str, list[str]] = {
    "README_MASTER": ["field", "value", "updated_at", "updated_by"],
    "IMPORT_LOG": [
        "import_batch_id",
        "run_id",
        "started_at",
        "finished_at",
        "status",
        "records_written",
        "records_skipped",
        "error_code",
        "error_message",
    ],
    "SOURCE_FILES": [
        "source_file_id",
        "original_filename",
        "file_hash",
        "file_type_detected",
        "source_priority",
        "ingested_at",
        "import_batch_id",
        "sensitivity_flag",
    ],
    "PROJECTS": [
        "project_id",
        "project_code",
        "project_name",
        "surface_base_value",
        "surface_base_unit",
        "surface_base_status",
        "created_at",
        "updated_at",
    ],
    "BUDGET_VERSIONS": [
        "budget_version_id",
        "project_id",
        "source_file_id",
        "version_name",
        "version_date",
        "is_latest_version",
        "validation_status",
        "import_batch_id",
    ],
    "RAW_IMPORTS": [
        "raw_import_id",
        "source_file_id",
        "raw_path_ref",
        "raw_hash",
        "ingested_at",
        "import_batch_id",
        "raw_access_policy",
    ],
    "COST_ITEMS": [
        "cost_item_id",
        "budget_version_id",
        "source_file_id",
        "origin_record_ref",
        "description_raw",
        "unit_raw",
        "quantity_raw",
        "unit_price_raw",
        "amount_raw",
        "row_hash",
        "validation_status",
    ],
    "NORMALIZED_COST_ITEMS": [
        "normalized_cost_item_id",
        "cost_item_id",
        "normalized_description",
        "normalized_unit",
        "normalized_quantity",
        "normalized_amount",
        "normalization_status",
        "normalization_rule_ref",
        "row_hash",
        "validation_status",
    ],
    "CATEGORY_MAPPING": [
        "mapping_id",
        "mapping_key",
        "target_category",
        "mapping_confidence",
        "mapping_status",
        "decision_source",
        "approved_by",
        "approved_at",
    ],
    "VALIDATION_RESULTS": [
        "validation_result_id",
        "entity_type",
        "entity_id",
        "rule_id",
        "severity",
        "status",
        "message",
        "validated_at",
        "import_batch_id",
    ],
    "RATIO_INPUTS": [
        "ratio_input_id",
        "normalized_cost_item_id",
        "project_id",
        "budget_version_id",
        "eligibility_status",
        "exclusion_flag",
        "validation_status",
        "effective_at",
    ],
    "RATIOS_CALCULATED": [
        "ratio_calc_id",
        "ratio_code",
        "project_scope",
        "input_version_ref",
        "calculated_value",
        "calculation_status",
        "calculated_at",
    ],
    "EXCLUSIONS": [
        "exclusion_id",
        "entity_type",
        "entity_id",
        "reason_code",
        "reason_detail",
        "is_reversible",
        "excluded_at",
        "excluded_by",
        "import_batch_id",
    ],
    "SNAPSHOTS": [
        "snapshot_id",
        "snapshot_ts",
        "master_version",
        "trigger_reason",
        "source_run_id",
        "storage_ref",
        "checksum",
        "created_by",
    ],
    "CHANGELOG": [
        "change_id",
        "change_ts",
        "change_type",
        "affected_sheet",
        "change_summary",
        "decision_ref",
        "applied_by",
    ],
}


class SchemaValidationError(RuntimeError):
    """Raised when workbook schema does not satisfy required contract."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _header_values(ws: object, expected_len: int) -> list[str]:
    return [
        str(getattr(ws.cell(row=1, column=idx), "value") or "").strip()
        for idx in range(1, expected_len + 1)
    ]


def validate_workbook_schema(workbook: Workbook) -> None:
    missing_sheets = [name for name in REQUIRED_SHEETS_COLUMNS if name not in workbook.sheetnames]
    if missing_sheets:
        raise SchemaValidationError(f"Missing required sheets: {', '.join(sorted(missing_sheets))}")

    for sheet_name, columns in REQUIRED_SHEETS_COLUMNS.items():
        ws = workbook[sheet_name]
        actual = _header_values(ws, len(columns))
        missing_columns = [col for col in columns if col not in actual]
        if missing_columns:
            raise SchemaValidationError(
                f"Sheet '{sheet_name}' missing required columns: {', '.join(missing_columns)}"
            )


def validate_workbook_file(path: Path) -> None:
    workbook = load_workbook(path)
    try:
        validate_workbook_schema(workbook)
    finally:
        workbook.close()


def _ensure_allowed_output(path: Path, root: Path) -> None:
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Output path must be inside '{root.as_posix()}': {path.as_posix()}") from exc


def _contains_allowed_anchor(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    for idx in range(len(parts) - 1):
        if parts[idx] == "outputs" and parts[idx + 1] == "live_excel_master":
            return True
    return False


def _create_workbook_template() -> Workbook:
    workbook = Workbook()
    default = workbook.active
    workbook.remove(default)

    for sheet_name, columns in REQUIRED_SHEETS_COLUMNS.items():
        ws = workbook.create_sheet(title=sheet_name)
        ws.append(columns)
        if sheet_name == "README_MASTER":
            ws.append(["master_contract_version", "phase_9_1_v1", utc_now_iso(), "system"])
            ws.append(["phase", "9.2", utc_now_iso(), "system"])
            ws.append(["real_data_allowed", "false", utc_now_iso(), "system"])

    return workbook


def _checksum_hint(path: Path) -> str:
    size = path.stat().st_size if path.exists() else 0
    return f"size:{size}"


def _snapshot_path(base_dir: Path, label: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return base_dir / f"{timestamp}_{label}_live_excel_master.xlsx"


def _copy_snapshot(src: Path, snapshots_dir: Path, label: str) -> Path:
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    dst = _snapshot_path(snapshots_dir, label)
    shutil.copy2(src, dst)
    return dst


def _append_row(ws: object, row: Iterable[str]) -> None:
    ws.append(list(row))


def generate_master(output_path: Path, update: bool) -> dict[str, str]:
    if not _contains_allowed_anchor(output_path):
        raise ValueError(
            "Output path must be inside an 'outputs/live_excel_master' directory."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshots_dir = output_path.parent / SNAPSHOTS_DIRNAME
    pre_snapshot_ref = ""
    post_snapshot_ref = ""

    if output_path.exists() and not update:
        raise RuntimeError(
            "Output workbook already exists. Use --update for controlled update with snapshots."
        )

    if output_path.exists():
        validate_workbook_file(output_path)
        pre_snapshot = _copy_snapshot(output_path, snapshots_dir, "pre")
        pre_snapshot_ref = pre_snapshot.as_posix()

    workbook = _create_workbook_template()

    if pre_snapshot_ref:
        snapshots_ws = workbook["SNAPSHOTS"]
        _append_row(
            snapshots_ws,
            [
                f"snp_pre_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                utc_now_iso(),
                "0.1.0",
                "pre_update",
                "phase_9_2_run",
                pre_snapshot_ref,
                _checksum_hint(Path(pre_snapshot_ref)),
                "system",
            ],
        )

    workbook.save(output_path)
    workbook.close()

    validate_workbook_file(output_path)

    if update:
        post_snapshot = _copy_snapshot(output_path, snapshots_dir, "post")
        post_snapshot_ref = post_snapshot.as_posix()

        wb_update = load_workbook(output_path)
        try:
            snapshots_ws = wb_update["SNAPSHOTS"]
            changelog_ws = wb_update["CHANGELOG"]
            _append_row(
                snapshots_ws,
                [
                    f"snp_post_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    utc_now_iso(),
                    "0.1.0",
                    "post_update",
                    "phase_9_2_run",
                    post_snapshot_ref,
                    _checksum_hint(Path(post_snapshot_ref)),
                    "system",
                ],
            )
            _append_row(
                changelog_ws,
                [
                    f"chg_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    utc_now_iso(),
                    "template_update",
                    "ALL",
                    "Controlled update with pre/post snapshots",
                    "phase_9_2_live_excel_master_generator_implementation",
                    "system",
                ],
            )
            wb_update.save(output_path)
        finally:
            wb_update.close()

    return {
        "output": output_path.as_posix(),
        "updated": str(update).lower(),
        "pre_snapshot": pre_snapshot_ref,
        "post_snapshot": post_snapshot_ref,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a controlled live Excel master template (phase 9.2)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Target .xlsx file path. Must be under outputs/live_excel_master.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Allow controlled update when output file already exists. Creates pre/post snapshots.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_path = (root / args.output).resolve()
    allowed_root = (root / ALLOWED_OUTPUT_ROOT).resolve()

    _ensure_allowed_output(output_path, allowed_root)
    result = generate_master(output_path=output_path, update=args.update)

    print("Live Excel master generator completed.")
    print(f"- Output: {result['output']}")
    print(f"- Updated existing workbook: {result['updated']}")
    print(f"- Pre snapshot: {result['pre_snapshot'] or 'n/a'}")
    print(f"- Post snapshot: {result['post_snapshot'] or 'n/a'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
