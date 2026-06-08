"""Router for POST /api/items/analisis (FASE C)."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter

from app import database as _db
from app.crud.item_master_ratios import (
    get_median_prices_por_categoria,
    get_ratio_by_categoria,
    update_ratio_incremental,
)
from app.schemas.items_analisis import (
    AnalisisItemsResponse,
    ItemAnalisisResultado,
    PresupuestoParaAnalisis,
    ResumenPorCategoria,
)
from app.services.clasificacion_service import clasificar_item_desde_descripcion
from app.services.items_service import (
    get_or_create_item_master as _get_or_create_item_master_service,
    normalize_item_key,
)
from src.db.schema import Confianza, ItemMaster

router = APIRouter(prefix="/api", tags=["items"])
logger = logging.getLogger(__name__)

# Confianza ordering: lower = weaker
_CONFIANZA_ORDEN: Dict[str, int] = {
    Confianza.MUY_DEBIL: 1,
    Confianza.DEBIL: 2,
    Confianza.SOLIDO: 3,
    Confianza.MUY_SOLIDO: 4,
}


@router.post("/items/analisis", response_model=AnalisisItemsResponse)
def analizar_items(presupuesto: PresupuestoParaAnalisis) -> AnalisisItemsResponse:
    """Classify items, compare against historical ratios, and update ratios."""
    session = _db.get_db()
    try:
        medianas = get_median_prices_por_categoria(session)
        items_resultados: List[ItemAnalisisResultado] = []
        # Collect (item_master_id, categoria, nuevo_valor) for deferred ratio update
        actualizaciones: List[tuple[int, str, float]] = []

        for item_input in presupuesto.items:
            # 1. Classify
            categoria = clasificar_item_desde_descripcion(
                item_input.descripcion,
                precio_unitario=item_input.precio_unitario,
                ratios_historicos=medianas,
            )
            categoria_str = categoria.value

            # 2. Get or create ItemMaster
            item_master = _get_or_create_item_master(session, item_input.descripcion, categoria_str)

            # 3. Get existing ratio (before update — response shows historical state)
            ratio_obj = get_ratio_by_categoria(session, item_master.id, categoria_str)
            ratio_historico = ratio_obj.ratio_actual if ratio_obj else None

            # 4. Calculate deviation
            if ratio_historico is not None:
                desviacion_pct = round(
                    (item_input.precio_unitario - ratio_historico) / ratio_historico * 100, 2
                )
                impacto = round(desviacion_pct * item_input.cantidad, 4)
            else:
                desviacion_pct = None
                impacto = None

            # 5. Confianza
            confianza = ratio_obj.confianza if ratio_obj else Confianza.MUY_DEBIL.value

            items_resultados.append(
                ItemAnalisisResultado(
                    descripcion=item_input.descripcion,
                    categoria=categoria_str,
                    precio_usuario=item_input.precio_unitario,
                    ratio_historico=ratio_historico,
                    desviacion_pct=desviacion_pct,
                    confianza=confianza,
                    impacto_monetario=impacto,
                    ratio_encontrado=ratio_historico is not None,
                )
            )

            actualizaciones.append((item_master.id, categoria_str, item_input.precio_unitario))

        # 6. Update ratios incrementally (after building results, so response shows pre-update state)
        for item_master_id, categoria_str, nuevo_valor in actualizaciones:
            update_ratio_incremental(session, item_master_id, categoria_str, nuevo_valor)

        session.commit()

        return AnalisisItemsResponse(
            items=items_resultados,
            resumenes_por_categoria=_generar_resumenes_por_categoria(items_resultados),
            resumen_general=_generar_resumen_general(items_resultados),
        )

    except Exception:
        session.rollback()
        logger.exception("Error in analizar_items")
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalizar_item_key(descripcion: str) -> str:
    """Normalize a description into a unique, lowercase, ASCII item_key.

    Delegated to centralized service: app.services.items_service.normalize_item_key

    "Carpintería Aluminio Doble" → "carpinteria_aluminio_doble"
    """
    return normalize_item_key(descripcion)


def _get_or_create_item_master(session: Any, descripcion: str, categoria_asignada: str) -> ItemMaster:
    """Get or create ItemMaster using centralized service."""
    item_key = normalize_item_key(descripcion)
    master = _get_or_create_item_master_service(
        session,
        item_key=item_key,
        categoria=None,
        subcategoria=None,
        unidad=None,
    )
    # Set categoria_asignada if it's provided and not already set
    if categoria_asignada and not master.categoria_asignada:
        master.categoria_asignada = categoria_asignada
    return master


def _generar_resumenes_por_categoria(
    items: List[ItemAnalisisResultado],
) -> Dict[str, ResumenPorCategoria]:
    grupos: dict[str, list[ItemAnalisisResultado]] = defaultdict(list)
    for item in items:
        grupos[item.categoria].append(item)

    resumenes: Dict[str, ResumenPorCategoria] = {}
    for categoria, grupo in grupos.items():
        precio_total = sum(i.precio_usuario for i in grupo)
        ratio_total = sum(i.ratio_historico for i in grupo if i.ratio_historico is not None)
        desviaciones = [i.desviacion_pct for i in grupo if i.desviacion_pct is not None]
        confianzas = [i.confianza for i in grupo]
        sin_ratio = sum(1 for i in grupo if not i.ratio_encontrado)

        desviacion_pct_promedio = (
            round(sum(desviaciones) / len(desviaciones), 2) if desviaciones else 0.0
        )
        confianza_global = min(confianzas, key=lambda c: _CONFIANZA_ORDEN.get(c, 1))

        resumenes[categoria] = ResumenPorCategoria(
            categoria=categoria,
            cantidad_items=len(grupo),
            precio_total_usuario=round(precio_total, 2),
            ratio_total_historico=round(ratio_total, 2),
            desviacion_pct_promedio=desviacion_pct_promedio,
            confianza_global=confianza_global,
            items_sin_ratio=sin_ratio,
        )

    return resumenes


def _generar_resumen_general(items: List[ItemAnalisisResultado]) -> Dict[str, Any]:
    total_usuario = sum(i.precio_usuario for i in items)
    total_ratio = sum(i.ratio_historico for i in items if i.ratio_historico is not None)
    diferencia = total_usuario - total_ratio
    diferencia_pct = round(diferencia / total_ratio * 100, 2) if total_ratio else 0.0
    con_ratio = sum(1 for i in items if i.ratio_encontrado)
    sin_ratio = len(items) - con_ratio

    return {
        "total_usuario": round(total_usuario, 2),
        "total_ratio": round(total_ratio, 2),
        "diferencia_pct": diferencia_pct,
        "items_con_ratio": con_ratio,
        "items_sin_ratio": sin_ratio,
    }
