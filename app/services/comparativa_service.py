"""Business logic for visualization endpoints."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.schemas.visuales import (
    CapituloRatioResponse,
    ComparativaCapitulo,
    ComparativaResponse,
    ItemPresupuesto,
    PresupuestoAnalisis,
    ResumenComparativa,
)
from src.db.schema import Ratio, ItemMaster

_CONFIABILIDAD_ORDEN = {"muy_solido": 4, "solido": 3, "debil": 2, "muy_debil": 1}


def calcular_estado_confiabilidad(cantidad_datos: int) -> str:
    cantidad_normalizada = max(int(cantidad_datos or 0), 0)
    if cantidad_normalizada >= 10:
        return "muy_solido"
    if cantidad_normalizada >= 5:
        return "solido"
    if cantidad_normalizada >= 2:
        return "debil"
    return "muy_debil"


def obtener_capitulos_ratios(
    session: Session,
    building_type: Optional[str] = None,
) -> List[CapituloRatioResponse]:
    """Return all items with consolidated statistics from item_master (not ratios table)."""
    q = session.query(ItemMaster)

    resultado: List[CapituloRatioResponse] = []
    for item in q.order_by(ItemMaster.item_key).all():
        resultado.append(
            CapituloRatioResponse(
                capitulo=item.categoria or "SIN_CATEGORIA",
                descripcion=item.item_key or "",
                minimo=item.min_unitario or 0.0,
                percentil_25=item.min_unitario or 0.0,
                mediana=item.mediana_unitario or item.media_unitario or 0.0,
                percentil_75=item.max_unitario or 0.0,
                maximo=item.max_unitario or 0.0,
                desviacion_std=item.desv_std or 0.0,
                cantidad_datos=int(item.muestras_count or 0),
                estado_confiabilidad=calcular_estado_confiabilidad(item.muestras_count or 0),
                building_type=None,
            )
        )
    return resultado


def analizar_comparativa(
    session: Session,
    presupuesto: PresupuestoAnalisis,
) -> ComparativaResponse:
    """Compare user budget against historical ratios chapter by chapter."""
    capitulos_resultado: List[ComparativaCapitulo] = []
    capitulos_sin_ratio: List[str] = []
    total_presupuesto = 0.0
    total_ratio = 0.0
    confiabilidades: List[str] = []

    items_por_capitulo: DefaultDict[str, List[ItemPresupuesto]] = defaultdict(list)
    for item in presupuesto.items:
        items_por_capitulo[_normalize_text(item.capitulo)].append(item)

    ratios_por_capitulo = _cargar_ratios_por_capitulo(
        session=session,
        chapter_codes=list(items_por_capitulo.keys()),
        building_type=presupuesto.building_type,
    )

    for capitulo_norm, items in items_por_capitulo.items():
        ratio_db = ratios_por_capitulo.get(capitulo_norm)

        if ratio_db is None or ratio_db.mediana_unitario is None:
            capitulos_sin_ratio.append(capitulo_norm)
            continue

        total_cantidad = sum(item.cantidad for item in items)
        valor_mio = sum(item.valor_unitario * item.cantidad for item in items) / total_cantidad
        valor_ratio = ratio_db.mediana_unitario
        desviacion_pct = ((valor_mio - valor_ratio) / valor_ratio * 100) if valor_ratio else 0.0
        impacto_monetario = (desviacion_pct / 100) * valor_ratio * presupuesto.area_total

        confiabilidad = calcular_estado_confiabilidad(ratio_db.muestras_count or 0)
        confiabilidades.append(confiabilidad)

        capitulos_resultado.append(
            ComparativaCapitulo(
                capitulo=capitulo_norm,
                descripcion=ratio_db.item_key,
                valor_mio=round(valor_mio, 4),
                valor_ratio=round(valor_ratio, 4),
                desviacion_pct=round(desviacion_pct, 2),
                impacto_monetario=round(impacto_monetario, 2),
                estado_confiabilidad=confiabilidad,
                ratio_encontrado=True,
            )
        )
        total_presupuesto += valor_mio * presupuesto.area_total
        total_ratio += valor_ratio * presupuesto.area_total

    confiabilidad_global = (
        min(confiabilidades, key=lambda value: _CONFIABILIDAD_ORDEN.get(value, 0))
        if confiabilidades
        else "muy_debil"
    )

    diferencia_monetaria = total_presupuesto - total_ratio
    diferencia_pct = (diferencia_monetaria / total_ratio * 100) if total_ratio else 0.0

    return ComparativaResponse(
        capitulos=capitulos_resultado,
        capitulos_sin_ratio=capitulos_sin_ratio,
        resumen=ResumenComparativa(
            total_presupuesto=round(total_presupuesto, 2),
            total_ratio=round(total_ratio, 2),
            diferencia_pct=round(diferencia_pct, 2),
            diferencia_monetaria=round(diferencia_monetaria, 2),
            area_total=presupuesto.area_total,
            confiabilidad_global=confiabilidad_global,
        ),
    )


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def _cargar_ratios_por_capitulo(
    session: Session,
    chapter_codes: List[str],
    building_type: Optional[str],
) -> dict[str, ItemMaster]:
    if not chapter_codes:
        return {}

    # Look for items by categoria matching chapter_codes
    rows = (
        session.query(ItemMaster)
        .filter(
            func.upper(ItemMaster.categoria).in_(chapter_codes),
            ItemMaster.mediana_unitario.isnot(None),
        )
        .all()
    )

    ratios_por_capitulo: dict[str, ItemMaster] = {}
    for row in rows:
        categoria = _normalize_text(row.categoria)
        if not categoria:
            continue
        if categoria not in ratios_por_capitulo:
            ratios_por_capitulo[categoria] = row

    return ratios_por_capitulo


def _buscar_ratio(
    session: Session, chapter_code: str, building_type: Optional[str]
) -> Optional[ItemMaster]:
    """Find an ItemMaster row for a given category."""
    normalized_chapter_code = _normalize_text(chapter_code)
    return (
        session.query(ItemMaster)
        .filter(func.upper(ItemMaster.categoria) == normalized_chapter_code)
        .first()
    )
