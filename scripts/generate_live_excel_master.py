#!/usr/bin/env python3
"""Create, update, and harden a controlled live Excel master template."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
from typing import Iterable
from uuid import uuid4

from openpyxl import Workbook, load_workbook  # type: ignore

DEFAULT_OUTPUT = Path("outputs/live_excel_master/live_excel_master.xlsx")
ALLOWED_OUTPUT_ROOT = Path("outputs/live_excel_master")
SNAPSHOTS_DIRNAME = "snapshots"
DEFAULT_RETENTION_MAX = 5
BLOCKED_STATUSES = {"BLOCKED", "ERROR", "VALIDATION_BLOCKED"}

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

SYNTHETIC_PK_COLUMNS = {
    "SOURCE_FILES": "source_file_id",
    "PROJECTS": "project_id",
    "BUDGET_VERSIONS": "budget_version_id",
    "IMPORT_LOG": "import_batch_id",
    "RAW_IMPORTS": "raw_import_id",
    "COST_ITEMS": "cost_item_id",
    "VALIDATION_RESULTS": "validation_result_id",
    "EXCLUSIONS": "exclusion_id",
    "RATIO_INPUTS": "ratio_input_id",
}

REQUIRED_NON_EMPTY_COLUMNS = {
    "BUDGET_VERSIONS": ["budget_version_id", "source_file_id", "validation_status"],
    "COST_ITEMS": ["cost_item_id", "budget_version_id", "source_file_id", "validation_status"],
    "NORMALIZED_COST_ITEMS": ["normalized_cost_item_id", "cost_item_id", "validation_status"],
    "RATIO_INPUTS": ["ratio_input_id", "budget_version_id", "validation_status"],
}


class SchemaValidationError(RuntimeError):
    """Raised when workbook schema does not satisfy required contract."""


class ReferentialValidationError(RuntimeError):
    """Raised when workbook data does not satisfy referential contract."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _header_values(ws: object, expected_len: int) -> list[str]:
    return [
        str(getattr(ws.cell(row=1, column=idx), "value") or "").strip()
        for idx in range(1, expected_len + 1)
    ]


def _sheet_dict_rows(workbook: Workbook, sheet_name: str) -> list[dict[str, str]]:
    ws = workbook[sheet_name]
    headers = REQUIRED_SHEETS_COLUMNS[sheet_name]
    rows: list[dict[str, str]] = []
    for row_idx in range(2, ws.max_row + 1):
        values = [ws.cell(row=row_idx, column=idx).value for idx in range(1, len(headers) + 1)]
        row_map = {headers[i]: ("" if values[i] is None else str(values[i]).strip()) for i in range(len(headers))}
        if any(row_map.values()):
            rows.append(row_map)
    return rows


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


def validate_referential_integrity(workbook: Workbook) -> None:
    source_rows = _sheet_dict_rows(workbook, "SOURCE_FILES")
    budget_rows = _sheet_dict_rows(workbook, "BUDGET_VERSIONS")
    raw_rows = _sheet_dict_rows(workbook, "RAW_IMPORTS")
    cost_rows = _sheet_dict_rows(workbook, "COST_ITEMS")
    validation_rows = _sheet_dict_rows(workbook, "VALIDATION_RESULTS")
    import_rows = _sheet_dict_rows(workbook, "IMPORT_LOG")
    exclusion_rows = _sheet_dict_rows(workbook, "EXCLUSIONS")
    ratio_input_rows = _sheet_dict_rows(workbook, "RATIO_INPUTS")

    source_ids = {row["source_file_id"] for row in source_rows if row["source_file_id"]}
    budget_ids = {row["budget_version_id"] for row in budget_rows if row["budget_version_id"]}
    import_batch_ids = {row["import_batch_id"] for row in import_rows if row["import_batch_id"]}
    excluded_cost_ids = {
        row["entity_id"]
        for row in exclusion_rows
        if row.get("entity_type", "").upper() == "COST_ITEM" and row.get("entity_id")
    }

    for sheet_name, pk_col in SYNTHETIC_PK_COLUMNS.items():
        seen: set[str] = set()
        for row in _sheet_dict_rows(workbook, sheet_name):
            pk = row.get(pk_col, "")
            if not pk:
                raise ReferentialValidationError(f"{sheet_name}.{pk_col} cannot be empty.")
            if pk in seen:
                raise ReferentialValidationError(f"Duplicate key found in {sheet_name}.{pk_col}: {pk}")
            seen.add(pk)

    for sheet_name, required_cols in REQUIRED_NON_EMPTY_COLUMNS.items():
        for row in _sheet_dict_rows(workbook, sheet_name):
            for col in required_cols:
                if not row.get(col):
                    raise ReferentialValidationError(f"{sheet_name}.{col} cannot be empty.")

    for row in budget_rows:
        ref = row.get("source_file_id", "")
        if ref and ref not in source_ids:
            raise ReferentialValidationError(
                f"BUDGET_VERSIONS.source_file_id not found in SOURCE_FILES: {ref}"
            )

    for row in cost_rows:
        budget_ref = row.get("budget_version_id", "")
        source_ref = row.get("source_file_id", "")
        if budget_ref and budget_ref not in budget_ids:
            raise ReferentialValidationError(
                f"COST_ITEMS.budget_version_id not found in BUDGET_VERSIONS: {budget_ref}"
            )
        if source_ref and source_ref not in source_ids:
            raise ReferentialValidationError(
                f"COST_ITEMS.source_file_id not found in SOURCE_FILES: {source_ref}"
            )

    for row in raw_rows:
        ref = row.get("source_file_id", "")
        if ref and ref not in source_ids:
            raise ReferentialValidationError(f"RAW_IMPORTS.source_file_id not found in SOURCE_FILES: {ref}")

    for row in validation_rows:
        ref = row.get("import_batch_id", "")
        if ref and ref not in import_batch_ids:
            raise ReferentialValidationError(
                f"VALIDATION_RESULTS.import_batch_id not found in IMPORT_LOG: {ref}"
            )

    # Contract limitation: EXCLUSIONS does not include source_file_id column.
    # Compatible check: when exclusion is SOURCE_FILE typed, entity_id must exist in SOURCE_FILES.
    for row in exclusion_rows:
        if row.get("entity_type", "").upper() == "SOURCE_FILE":
            source_entity = row.get("entity_id", "")
            if source_entity and source_entity not in source_ids:
                raise ReferentialValidationError(
                    f"EXCLUSIONS SOURCE_FILE entity_id not found in SOURCE_FILES: {source_entity}"
                )

    for row in ratio_input_rows:
        status = row.get("validation_status", "").upper()
        if status in BLOCKED_STATUSES:
            raise ReferentialValidationError(
                "RATIO_INPUTS contains blocked/error validation_status; promotion must be blocked."
            )
        budget_ref = row.get("budget_version_id", "")
        if budget_ref and budget_ref not in budget_ids:
            raise ReferentialValidationError(
                f"RATIO_INPUTS.budget_version_id not found in BUDGET_VERSIONS: {budget_ref}"
            )

    for row in ratio_input_rows:
        normalized_ref = row.get("normalized_cost_item_id", "")
        if normalized_ref and normalized_ref in excluded_cost_ids:
            raise ReferentialValidationError(
                "RATIO_INPUTS contains excluded item reference."
            )


def validate_workbook_file(path: Path) -> None:
    workbook = load_workbook(path)
    try:
        validate_workbook_schema(workbook)
        validate_referential_integrity(workbook)
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


def _create_workbook_template(phase_value: str = "9.3") -> Workbook:
    workbook = Workbook()
    default = workbook.active
    workbook.remove(default)

    for sheet_name, columns in REQUIRED_SHEETS_COLUMNS.items():
        ws = workbook.create_sheet(title=sheet_name)
        ws.append(columns)
        if sheet_name == "README_MASTER":
            ws.append(["master_contract_version", "phase_9_1_v1", utc_now_iso(), "system"])
            ws.append(["phase", phase_value, utc_now_iso(), "system"])
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


def _write_snapshot_log(workbook: Workbook, trigger: str, run_id: str, storage_ref: str) -> None:
    snapshots_ws = workbook["SNAPSHOTS"]
    _append_row(
        snapshots_ws,
        [
            f"snp_{trigger}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            utc_now_iso(),
            "0.1.0",
            trigger,
            run_id,
            storage_ref,
            _checksum_hint(Path(storage_ref)),
            "system",
        ],
    )


def _apply_snapshot_retention(snapshots_dir: Path, keep_last: int) -> list[str]:
    if keep_last <= 0 or not snapshots_dir.exists():
        return []
    files = sorted([p for p in snapshots_dir.glob("*.xlsx") if p.is_file()], key=lambda p: p.stat().st_mtime)
    to_delete = files[:-keep_last] if len(files) > keep_last else []
    deleted: list[str] = []
    for path in to_delete:
        deleted.append(path.as_posix())
        path.unlink(missing_ok=True)
    return deleted


def _add_synthetic_incremental_rows(workbook: Workbook, run_id: str) -> None:
    ts = utc_now_iso()
    import_batch_id = f"imp_{run_id}"
    source_file_id = f"sf_{run_id}"
    project_id = f"prj_{run_id}"
    budget_version_id = f"bv_{run_id}"
    raw_import_id = f"raw_{run_id}"
    cost_item_id_ok = f"ci_ok_{run_id}"
    cost_item_id_blocked = f"ci_blk_{run_id}"
    validation_result_id = f"vr_{run_id}"
    exclusion_id = f"ex_{run_id}"
    ratio_input_id = f"ri_{run_id}"

    _append_row(
        workbook["IMPORT_LOG"],
        [import_batch_id, run_id, ts, ts, "SYNTHETIC_OK", "2", "1", "", ""],
    )
    _append_row(
        workbook["SOURCE_FILES"],
        [
            source_file_id,
            f"synthetic_{run_id}.xlsx",
            f"synthetic_hash_{run_id}",
            "SYNTHETIC_XLSX",
            "LOW",
            ts,
            import_batch_id,
            "NON_SENSITIVE",
        ],
    )
    _append_row(
        workbook["PROJECTS"],
        [project_id, f"P-{run_id[:8]}", "Synthetic Project", "", "m2", "PENDING", ts, ts],
    )
    _append_row(
        workbook["BUDGET_VERSIONS"],
        [budget_version_id, project_id, source_file_id, "v_synth_1", ts[:10], "true", "VALIDATED", import_batch_id],
    )
    _append_row(
        workbook["RAW_IMPORTS"],
        [raw_import_id, source_file_id, f"raw://synthetic/{run_id}", f"raw_hash_{run_id}", ts, import_batch_id, "DENY"],
    )
    _append_row(
        workbook["COST_ITEMS"],
        [
            cost_item_id_ok,
            budget_version_id,
            source_file_id,
            "A-001",
            "Synthetic cost item OK",
            "ud",
            "1",
            "100.00",
            "100.00",
            f"row_hash_{cost_item_id_ok}",
            "VALIDATED",
        ],
    )
    _append_row(
        workbook["COST_ITEMS"],
        [
            cost_item_id_blocked,
            budget_version_id,
            source_file_id,
            "A-002",
            "Synthetic cost item BLOCKED",
            "ud",
            "1",
            "200.00",
            "200.00",
            f"row_hash_{cost_item_id_blocked}",
            "BLOCKED",
        ],
    )
    _append_row(
        workbook["VALIDATION_RESULTS"],
        [
            validation_result_id,
            "COST_ITEM",
            cost_item_id_ok,
            "RULE_SYNTH_001",
            "INFO",
            "PASS",
            "synthetic validation result",
            ts,
            import_batch_id,
        ],
    )
    _append_row(
        workbook["EXCLUSIONS"],
        [
            exclusion_id,
            "COST_ITEM",
            cost_item_id_blocked,
            "BLOCKED_STATUS",
            "blocked synthetic item",
            "true",
            ts,
            "system",
            import_batch_id,
        ],
    )
    _append_row(
        workbook["RATIO_INPUTS"],
        [
            ratio_input_id,
            f"norm_{cost_item_id_ok}",
            project_id,
            budget_version_id,
            "SYNTHETIC_ELIGIBLE",
            "false",
            "VALIDATED",
            ts,
        ],
    )
    _append_row(
        workbook["CHANGELOG"],
        [
            f"chg_{run_id}",
            ts,
            "synthetic_incremental_load",
            "MULTI",
            "Synthetic incremental load (non-operational ratios placeholders only)",
            "phase_9_3_live_excel_master_hardening",
            "system",
        ],
    )


def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _create_pre_snapshot_if_needed(output_path: Path, snapshots_dir: Path, run_id: str) -> str:
    if not output_path.exists():
        return ""
    validate_workbook_file(output_path)
    pre_snapshot = _copy_snapshot(output_path, snapshots_dir, "pre_update")
    return pre_snapshot.as_posix()


def _finalize_post_snapshot(
    output_path: Path,
    snapshots_dir: Path,
    workbook_root: Path,
    retention_max: int,
    run_id: str,
) -> tuple[str, list[str]]:
    post_snapshot = _copy_snapshot(output_path, snapshots_dir, "post_update")
    post_ref = post_snapshot.as_posix()
    deleted = _apply_snapshot_retention(snapshots_dir, retention_max)

    wb = load_workbook(output_path)
    try:
        _write_snapshot_log(wb, "post_update", run_id, _safe_relative_path(post_snapshot, workbook_root))
        for deleted_ref in deleted:
            _append_row(
                wb["CHANGELOG"],
                [
                    f"chg_ret_{uuid4().hex[:12]}",
                    utc_now_iso(),
                    "snapshot_retention_delete",
                    "SNAPSHOTS",
                    f"Deleted snapshot due to retention policy: {deleted_ref}",
                    "phase_9_3_live_excel_master_hardening",
                    "system",
                ],
            )
        wb.save(output_path)
    finally:
        wb.close()

    return post_ref, deleted


def generate_master(output_path: Path, update: bool, retention_max: int = DEFAULT_RETENTION_MAX) -> dict[str, str]:
    if not _contains_allowed_anchor(output_path):
        raise ValueError("Output path must be inside an 'outputs/live_excel_master' directory.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshots_dir = output_path.parent / SNAPSHOTS_DIRNAME
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}"
    pre_snapshot_ref = ""
    post_snapshot_ref = ""

    if output_path.exists() and not update:
        raise RuntimeError("Output workbook already exists. Use --update for controlled update with snapshots.")

    if output_path.exists():
        pre_snapshot_ref = _create_pre_snapshot_if_needed(output_path, snapshots_dir, run_id)

    workbook = _create_workbook_template("9.3")
    if pre_snapshot_ref:
        _write_snapshot_log(workbook, "pre_update", run_id, pre_snapshot_ref)
    workbook.save(output_path)
    workbook.close()

    validate_workbook_file(output_path)

    if update:
        post_snapshot_ref, _ = _finalize_post_snapshot(
            output_path=output_path,
            snapshots_dir=snapshots_dir,
            workbook_root=output_path.parent.parent.parent,
            retention_max=retention_max,
            run_id=run_id,
        )
        wb_update = load_workbook(output_path)
        try:
            _append_row(
                wb_update["CHANGELOG"],
                [
                    f"chg_{uuid4().hex[:12]}",
                    utc_now_iso(),
                    "template_update",
                    "ALL",
                    "Controlled template update with pre/post snapshots",
                    "phase_9_3_live_excel_master_hardening",
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


def load_synthetic_incremental(
    output_path: Path,
    retention_max: int = DEFAULT_RETENTION_MAX,
) -> dict[str, str]:
    if not _contains_allowed_anchor(output_path):
        raise ValueError("Output path must be inside an 'outputs/live_excel_master' directory.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshots_dir = output_path.parent / SNAPSHOTS_DIRNAME
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}"

    if output_path.exists():
        pre_snapshot = _create_pre_snapshot_if_needed(output_path, snapshots_dir, run_id)
    else:
        pre_snapshot = ""
        wb_seed = _create_workbook_template("9.3")
        wb_seed.save(output_path)
        wb_seed.close()

    wb = load_workbook(output_path)
    try:
        validate_workbook_schema(wb)
        _add_synthetic_incremental_rows(wb, run_id)
        if pre_snapshot:
            _write_snapshot_log(wb, "pre_update", run_id, pre_snapshot)
        wb.save(output_path)
    finally:
        wb.close()

    validate_workbook_file(output_path)

    post_snapshot_ref, deleted = _finalize_post_snapshot(
        output_path=output_path,
        snapshots_dir=snapshots_dir,
        workbook_root=output_path.parent.parent.parent,
        retention_max=retention_max,
        run_id=run_id,
    )

    return {
        "output": output_path.as_posix(),
        "run_id": run_id,
        "pre_snapshot": pre_snapshot,
        "post_snapshot": post_snapshot_ref,
        "deleted_snapshots": str(len(deleted)),
    }


def rollback_master_from_snapshot(
    output_path: Path,
    snapshot_path: Path,
    retention_max: int = DEFAULT_RETENTION_MAX,
) -> dict[str, str]:
    if not output_path.exists():
        raise RuntimeError("Cannot rollback non-existing master workbook.")
    if not snapshot_path.exists():
        raise RuntimeError("Snapshot path does not exist.")
    if not _contains_allowed_anchor(output_path):
        raise ValueError("Output path must be inside an 'outputs/live_excel_master' directory.")

    snapshots_dir = output_path.parent / SNAPSHOTS_DIRNAME
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}"
    pre_snapshot = _create_pre_snapshot_if_needed(output_path, snapshots_dir, run_id)

    shutil.copy2(snapshot_path, output_path)
    validate_workbook_file(output_path)

    wb = load_workbook(output_path)
    try:
        _write_snapshot_log(wb, "rollback", run_id, snapshot_path.as_posix())
        _append_row(
            wb["CHANGELOG"],
            [
                f"chg_rb_{uuid4().hex[:12]}",
                utc_now_iso(),
                "rollback_apply",
                "ALL",
                f"Rollback applied from snapshot {snapshot_path.name}",
                "phase_9_3_live_excel_master_hardening",
                "system",
            ],
        )
        wb.save(output_path)
    finally:
        wb.close()

    post_snapshot_ref, deleted = _finalize_post_snapshot(
        output_path=output_path,
        snapshots_dir=snapshots_dir,
        workbook_root=output_path.parent.parent.parent,
        retention_max=retention_max,
        run_id=run_id,
    )

    return {
        "output": output_path.as_posix(),
        "run_id": run_id,
        "pre_snapshot": pre_snapshot,
        "post_snapshot": post_snapshot_ref,
        "deleted_snapshots": str(len(deleted)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and harden a controlled live Excel master template (phase 9.3)."
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
        help="Allow controlled template update when output file already exists.",
    )
    parser.add_argument(
        "--synthetic-load",
        action="store_true",
        help="Append one synthetic incremental batch to the master workbook.",
    )
    parser.add_argument(
        "--rollback-from",
        type=Path,
        default=None,
        help="Restore workbook from a snapshot path, then validate and snapshot again.",
    )
    parser.add_argument(
        "--snapshot-retention-max",
        type=int,
        default=DEFAULT_RETENTION_MAX,
        help="Keep at most N snapshot files in outputs/live_excel_master/snapshots.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.snapshot_retention_max < 1:
        raise ValueError("--snapshot-retention-max must be >= 1")

    root = Path(__file__).resolve().parents[1]
    output_path = (root / args.output).resolve()
    allowed_root = (root / ALLOWED_OUTPUT_ROOT).resolve()
    _ensure_allowed_output(output_path, allowed_root)

    if args.rollback_from is not None:
        snapshot_path = (root / args.rollback_from).resolve() if not args.rollback_from.is_absolute() else args.rollback_from
        result = rollback_master_from_snapshot(
            output_path=output_path,
            snapshot_path=snapshot_path,
            retention_max=args.snapshot_retention_max,
        )
        print("Live Excel master rollback completed.")
    elif args.synthetic_load:
        result = load_synthetic_incremental(
            output_path=output_path,
            retention_max=args.snapshot_retention_max,
        )
        print("Live Excel synthetic incremental load completed.")
    else:
        result = generate_master(
            output_path=output_path,
            update=args.update,
            retention_max=args.snapshot_retention_max,
        )
        print("Live Excel master template generation completed.")

    for key, value in result.items():
        print(f"- {key}: {value or 'n/a'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
