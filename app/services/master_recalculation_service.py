"""Canonical master recalculation after an APPROVED import."""

from __future__ import annotations

import statistics
from pathlib import Path

from sqlalchemy.orm import Session

from app.utils.excel_export import resolve_official_master_export_path
from src.db.queries import get_budget_by_hash, list_approved_budgets
from src.db.schema import Budget, BudgetImport, LineItem, Ratio
from src.export.excel_master_generator import generate_master_excel_approved


class MasterRecalculationError(Exception):
    """Raised when canonical post-approval recalculation cannot proceed."""


def _collect_approved_ratio_values(
    session: Session,
    chapter_code: str,
    building_type: str | None,
) -> list[float]:
    """Collect €/m² values using only APPROVED budgets."""
    rows = (
        session.query(LineItem, Budget, BudgetImport)
        .join(Budget, LineItem.budget_id == Budget.id)
        .join(BudgetImport, Budget.file_hash == BudgetImport.file_hash)
        .filter(
            BudgetImport.approval_status == "APPROVED",
            LineItem.chapter_code == chapter_code,
            LineItem.validation_status == "VALID",
            Budget.surface_m2.is_not(None),
            Budget.surface_m2 > 0,
        )
    )
    if building_type is not None:
        rows = rows.filter(Budget.building_type == building_type)
    else:
        rows = rows.filter(Budget.building_type.is_(None))

    values: list[float] = []
    for item, budget, _import in rows.all():
        if item.total_cost is not None and budget.surface_m2:
            values.append(item.total_cost / budget.surface_m2)
    return values


def recalculate_after_approval(session: Session, import_id: int) -> dict:
    """Recalculate canonical master data after an import becomes APPROVED."""
    record = session.query(BudgetImport).filter_by(id=import_id).first()
    if record is None:
        raise MasterRecalculationError(f"BudgetImport con id={import_id} no encontrado.")
    if record.approval_status != "APPROVED":
        raise MasterRecalculationError(
            f"No se puede recalcular el master para id={import_id}: "
            f"approval_status actual={record.approval_status!r}. Debe ser APPROVED."
        )

    budget = get_budget_by_hash(session, record.file_hash)
    if budget is None:
        raise MasterRecalculationError(
            f"No existe Budget asociado a BudgetImport id={import_id} "
            f"(file_hash={record.file_hash[:8]}...)."
        )

    warnings: list[str] = [
        "T6.5 no recalcula ItemMaster ni ItemMasterRatio en modo approved-only; "
        "esa deuda queda pendiente para una tarea posterior."
    ]

    approved_budgets = list_approved_budgets(session)
    distinct_pairs = (
        session.query(LineItem.chapter_code, Budget.building_type)
        .join(Budget, LineItem.budget_id == Budget.id)
        .join(BudgetImport, Budget.file_hash == BudgetImport.file_hash)
        .filter(
            BudgetImport.approval_status == "APPROVED",
            LineItem.validation_status == "VALID",
        )
        .distinct()
        .all()
    )

    session.query(Ratio).delete()
    ratios_recalculated = 0

    for chapter_code, building_type in distinct_pairs:
        values = _collect_approved_ratio_values(session, chapter_code, building_type)
        any_item_query = (
            session.query(LineItem)
            .join(Budget, LineItem.budget_id == Budget.id)
            .join(BudgetImport, Budget.file_hash == BudgetImport.file_hash)
            .filter(
                BudgetImport.approval_status == "APPROVED",
                LineItem.chapter_code == chapter_code,
                LineItem.validation_status == "VALID",
            )
        )
        if building_type is not None:
            any_item_query = any_item_query.filter(Budget.building_type == building_type)
        else:
            any_item_query = any_item_query.filter(Budget.building_type.is_(None))
        any_item = any_item_query.first()

        if not values:
            continue

        ratio = Ratio(
            chapter_code=chapter_code,
            chapter_name=any_item.chapter_name if any_item else chapter_code,
            building_type=building_type,
        )
        sorted_values = sorted(values)
        n = len(sorted_values)
        ratio.median = statistics.median(sorted_values)
        ratio.min_value = sorted_values[0]
        ratio.max_value = sorted_values[-1]
        ratio.cost_per_m2 = ratio.median
        ratio.sample_count = n
        if n >= 2:
            quartiles = statistics.quantiles(sorted_values, n=4)
            ratio.percentil_25 = quartiles[0]
            ratio.percentil_75 = quartiles[2]
            ratio.std_dev = statistics.stdev(sorted_values)
        else:
            ratio.percentil_25 = sorted_values[0]
            ratio.percentil_75 = sorted_values[0]
            ratio.std_dev = 0.0
        session.add(ratio)
        ratios_recalculated += 1

    if not approved_budgets:
        warnings.append("No hay budgets APPROVED; el workbook se exporta vacío.")
    elif ratios_recalculated == 0:
        warnings.append(
            "No se recalcularon filas de ratios approved-only. "
            "Los budgets APPROVED actuales no aportan LineItem con surface_m2 válida."
        )

    session.flush()
    export_path = Path(
        generate_master_excel_approved(
            session,
            output_path=resolve_official_master_export_path(),
        )
    )
    session.flush()

    return {
        "import_id": record.id,
        "budget_id": budget.id,
        "ratios_recalculated": ratios_recalculated,
        "master_exported": export_path.exists(),
        "warnings": warnings,
    }
