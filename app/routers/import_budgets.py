"""Router for POST /api/import/budgets — JSON budget import with deduplication."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from app import database as _db
from app.crud.budgets import (
    create_budget_import,
    get_budget_import_by_hash,
    update_budget_import_status,
)
from app.crud.items import get_or_create_item_master
from app.schemas.import_budgets import BudgetImportRequest, BudgetImportResponse
from app.utils.normalize import normalize_item_key

router = APIRouter(prefix="/api", tags=["import"])
logger = logging.getLogger(__name__)


@router.post("/import/budgets", response_model=BudgetImportResponse)
def import_budgets(request: BudgetImportRequest) -> BudgetImportResponse:
    """
    Importar presupuesto en formato JSON con deduplicación automática via item_key.

    - 409 si file_hash ya existe.
    - Líneas inválidas (sin descripción, cantidad≤0, precio≤0) se saltan con warning.
    - Misma descripción normalizada en un mismo payload → un solo ItemMaster.
    """
    from src.db.schema import Budget, ItemInstance, ItemMaster

    log_id = str(uuid.uuid4())[:8]
    start_time = datetime.now(timezone.utc)

    logger.info(
        "[Import %s] INICIADO: archivo=%s, lineas=%d, building_type=%s",
        log_id, request.filename, len(request.lineas), request.building_type,
    )

    session = _db.get_db()
    try:
        # ── 1. Detectar re-importación ─────────────────────────────────────
        existing = get_budget_import_by_hash(session, request.file_hash)
        if existing:
            fecha = (
                existing.import_date.strftime("%Y-%m-%d")
                if existing.import_date
                else "fecha desconocida"
            )
            raise HTTPException(
                status_code=409,
                detail=f"Ya importado el {fecha} (hash={request.file_hash[:8]}...)",
            )

        # ── 2. Registro de tracking ────────────────────────────────────────
        import_record = create_budget_import(
            session,
            filename=request.filename,
            file_hash=request.file_hash,
            building_type=request.building_type,
        )

        # ── 3. Budget padre (FK requerida por ItemInstance) ────────────────
        budget = Budget(
            filename=request.filename,
            file_hash=request.file_hash,
            source_format="json_api",
            building_type=request.building_type,
        )
        session.add(budget)
        session.flush()

        # ── 4. Procesar líneas ─────────────────────────────────────────────
        seen_keys: set[str] = set()
        items_creados = 0
        items_duplicados = 0
        items_errores = 0
        muestras_actualizadas = 0
        detalles: List[str] = []

        for linea in request.lineas:
            desc = (linea.descripcion or "").strip()
            if not desc:
                items_errores += 1
                detalles.append(f"Línea {linea.numero}: descripción vacía, omitida")
                logger.warning("[Import %s] Línea %d omitida: descripción vacía", log_id, linea.numero)
                continue

            if linea.cantidad is None or linea.cantidad <= 0:
                items_errores += 1
                detalles.append(f"Línea {linea.numero} ({desc!r}): cantidad inválida, omitida")
                logger.warning("[Import %s] Línea %d omitida: cantidad=%s", log_id, linea.numero, linea.cantidad)
                continue

            if linea.precio_unitario is None or linea.precio_unitario <= 0:
                items_errores += 1
                detalles.append(f"Línea {linea.numero} ({desc!r}): precio_unitario inválido, omitida")
                logger.warning("[Import %s] Línea %d omitida: precio_unitario=%s", log_id, linea.numero, linea.precio_unitario)
                continue

            item_key = normalize_item_key(desc)
            if not item_key:
                items_errores += 1
                detalles.append(f"Línea {linea.numero}: item_key vacío tras normalizar, omitida")
                continue

            # ¿Ya existía en BD antes de este import?
            pre_existing = (
                session.query(ItemMaster).filter_by(item_key=item_key).first()
            )
            is_new_in_db = pre_existing is None
            is_new_in_batch = item_key not in seen_keys

            master = get_or_create_item_master(
                session,
                item_key=item_key,
                categoria=request.building_type,
                subcategoria=None,
                unidad=linea.unidad or "ud",
            )

            if is_new_in_db and is_new_in_batch:
                items_creados += 1
                detalles.append(f"ItemMaster creado: {item_key!r}")
                logger.debug("[Import %s] Item nuevo: %s", log_id, item_key)
            else:
                items_duplicados += 1
                logger.debug("[Import %s] Item duplicado (reutilizado): %s", log_id, item_key)

            seen_keys.add(item_key)
            master.muestras_count = (master.muestras_count or 0) + 1
            muestras_actualizadas += 1

            instance = ItemInstance(
                budget_id=budget.id,
                item_master_id=master.id,
                descripcion=desc,
                categoria_original=linea.capitulo or "",
                unidad=linea.unidad or "ud",
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                precio_total=round(linea.cantidad * linea.precio_unitario, 4),
                validation_status="VALID",
            )
            session.add(instance)

        # ── 5. Status final ────────────────────────────────────────────────
        total_lineas = len(request.lineas)
        lineas_procesadas = items_creados + items_duplicados
        if lineas_procesadas == 0:
            final_status = "error"
        elif lineas_procesadas < total_lineas:
            final_status = "partial"
        else:
            final_status = "success"

        update_budget_import_status(
            session,
            import_record,
            status=final_status,
            items_count=lineas_procesadas,
        )

        session.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            "[Import %s] COMPLETADO en %.2fs: creados=%d, duplicados=%d, errores=%d, status=%s",
            log_id, elapsed, items_creados, items_duplicados, items_errores, final_status,
        )

        return BudgetImportResponse(
            import_id=str(import_record.id),
            items_creados=items_creados,
            items_duplicados=items_duplicados,
            muestras_actualizadas=muestras_actualizadas,
            detalles=detalles,
            status=final_status,
        )

    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        session.rollback()
        logger.error(
            "[Import %s] ERROR después de %.2fs: %s", log_id, elapsed, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error al importar: {exc}") from exc
    finally:
        session.close()
