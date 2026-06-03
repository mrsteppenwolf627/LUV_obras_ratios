"""Servicio centralizado de ingesta de presupuestos con deduplicación."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.crud.budgets import (
    create_budget_import,
    get_budget_import_by_hash,
    update_budget_import_status,
)
from app.crud.items import get_or_create_item_master
from app.schemas.import_budgets import BudgetImportResponse, LineaPresupuesto
from app.utils.normalize import normalize_item_key

logger = logging.getLogger(__name__)


class DuplicateImportError(Exception):
    """Raised when file_hash already exists in budget_imports."""

    def __init__(self, file_hash: str, import_date: str) -> None:
        self.file_hash = file_hash
        self.import_date = import_date
        super().__init__(f"Ya importado el {import_date} (hash={file_hash[:8]}...)")


class ImportService:
    """Orquesta la ingesta de un presupuesto: deduplicación, trazabilidad y logging."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._log_id = str(uuid.uuid4())[:8]
        self._start = datetime.now(timezone.utc)

    def importar(
        self,
        filename: str,
        file_hash: str,
        building_type: str,
        lineas: List[LineaPresupuesto],
    ) -> BudgetImportResponse:
        """
        Procesar un presupuesto completo.

        Raises:
            DuplicateImportError: si file_hash ya existe (el router lo convierte a 409).
        """
        from src.db.schema import Budget, ItemInstance, ItemMaster

        logger.info(
            "[Import %s] INICIADO: archivo=%s, lineas=%d, building_type=%s",
            self._log_id, filename, len(lineas), building_type,
        )

        # ── 1. Re-import guard ─────────────────────────────────────────────
        existing = get_budget_import_by_hash(self.session, file_hash)
        if existing:
            fecha = (
                existing.import_date.strftime("%Y-%m-%d")
                if existing.import_date
                else "fecha desconocida"
            )
            raise DuplicateImportError(file_hash, fecha)

        # ── 2. Tracking record ─────────────────────────────────────────────
        import_record = create_budget_import(
            self.session,
            filename=filename,
            file_hash=file_hash,
            building_type=building_type,
        )

        # ── 3. Budget padre (FK requerida por ItemInstance) ────────────────
        budget = Budget(
            filename=filename,
            file_hash=file_hash,
            source_format="json_api",
            building_type=building_type,
        )
        self.session.add(budget)
        self.session.flush()

        # ── 4. Procesar líneas ─────────────────────────────────────────────
        seen_keys: set[str] = set()
        items_creados = 0
        items_duplicados = 0
        items_errores = 0
        muestras_actualizadas = 0
        detalles: List[str] = []

        for linea in lineas:
            desc = (linea.descripcion or "").strip()
            if not desc:
                items_errores += 1
                detalles.append(f"Línea {linea.numero}: descripción vacía, omitida")
                logger.warning("[Import %s] Línea %d omitida: descripción vacía", self._log_id, linea.numero)
                continue

            if linea.cantidad is None or linea.cantidad <= 0:
                items_errores += 1
                detalles.append(f"Línea {linea.numero} ({desc!r}): cantidad inválida, omitida")
                logger.warning("[Import %s] Línea %d omitida: cantidad=%s", self._log_id, linea.numero, linea.cantidad)
                continue

            if linea.precio_unitario is None or linea.precio_unitario <= 0:
                items_errores += 1
                detalles.append(f"Línea {linea.numero} ({desc!r}): precio_unitario inválido, omitida")
                logger.warning("[Import %s] Línea %d omitida: precio_unitario=%s", self._log_id, linea.numero, linea.precio_unitario)
                continue

            item_key = normalize_item_key(desc)
            if not item_key:
                items_errores += 1
                detalles.append(f"Línea {linea.numero}: item_key vacío tras normalizar, omitida")
                continue

            pre_existing = self.session.query(ItemMaster).filter_by(item_key=item_key).first()
            is_new_in_db = pre_existing is None
            is_new_in_batch = item_key not in seen_keys

            master = get_or_create_item_master(
                self.session,
                item_key=item_key,
                categoria=building_type,
                subcategoria=None,
                unidad=linea.unidad or "ud",
            )

            if is_new_in_db and is_new_in_batch:
                items_creados += 1
                detalles.append(f"ItemMaster creado: {item_key!r}")
                logger.debug("[Import %s] Item nuevo: %s", self._log_id, item_key)
            else:
                items_duplicados += 1
                logger.debug("[Import %s] Item duplicado (reutilizado): %s", self._log_id, item_key)

            seen_keys.add(item_key)
            master.muestras_count = (master.muestras_count or 0) + 1
            muestras_actualizadas += 1

            self.session.add(ItemInstance(
                budget_id=budget.id,
                item_master_id=master.id,
                descripcion=desc,
                categoria_original=linea.capitulo or "",
                unidad=linea.unidad or "ud",
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                precio_total=round(linea.cantidad * linea.precio_unitario, 4),
                validation_status="VALID",
            ))

        # ── 5. Status final ────────────────────────────────────────────────
        total_lineas = len(lineas)
        lineas_procesadas = items_creados + items_duplicados
        if lineas_procesadas == 0:
            final_status = "error"
        elif lineas_procesadas < total_lineas:
            final_status = "partial"
        else:
            final_status = "success"

        update_budget_import_status(
            self.session,
            import_record,
            status=final_status,
            items_count=lineas_procesadas,
        )

        self.session.commit()

        elapsed = (datetime.now(timezone.utc) - self._start).total_seconds()
        logger.info(
            "[Import %s] COMPLETADO en %.2fs: creados=%d, duplicados=%d, errores=%d, status=%s",
            self._log_id, elapsed, items_creados, items_duplicados, items_errores, final_status,
        )

        return BudgetImportResponse(
            import_id=str(import_record.id),
            items_creados=items_creados,
            items_duplicados=items_duplicados,
            muestras_actualizadas=muestras_actualizadas,
            detalles=detalles,
            status=final_status,
        )
