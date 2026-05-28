"""Business logic for visualization endpoints."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.schema import Ratio
from app.schemas.visuales import (
    CapituloRatioResponse,
    ComparativaCapitulo,
    ComparativaResponse,
    PresupuestoAnalisis,
    ResumenComparativa,
)

_CONFIABILIDAD_ORDEN = {"muy_solido": 4, "solido": 3, "debil": 2, "muy_debil": 1}


def calcular_estado_confiabilidad(cantidad_datos: int) -> str:
    if cantidad_datos >= 10:
        return "muy_solido"
    if cantidad_datos >= 5:
        return "solido"
    if cantidad_datos >= 2:
        return "debil"
    return "muy_debil"


def obtener_capitulos_ratios(
    session: Session,
    building_type: Optional[str] = None,
) -> List[CapituloRatioResponse]:
    """Return all chapters that have a computed median ratio."""
    q = session.query(Ratio).filter(Ratio.median.isnot(None))
    if building_type:
        q = q.filter(func.upper(Ratio.building_type) == building_type.upper())

    resultado: List[CapituloRatioResponse] = []
    for ratio in q.order_by(Ratio.chapter_code).all():
        resultado.append(
            CapituloRatioResponse(
                capitulo=ratio.chapter_code,
                descripcion=ratio.chapter_name,
                minimo=ratio.min_value,
                percentil_25=ratio.percentil_25,
                mediana=ratio.median,
                percentil_75=ratio.percentil_75,
                maximo=ratio.max_value,
                desviacion_std=ratio.std_dev,
                cantidad_datos=ratio.sample_count,
                estado_confiabilidad=calcular_estado_confiabilidad(ratio.sample_count),
                building_type=ratio.building_type,
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

    # Group items by chapter (uppercase-normalized)
    items_por_capitulo: dict = {}
    for item in presupuesto.items:
        key = item.capitulo.upper().strip()
        items_por_capitulo.setdefault(key, []).append(item)

    for capitulo_norm, items in items_por_capitulo.items():
        # Look up historical ratio: prefer building_type match, fall back to any
        ratio_db = _buscar_ratio(session, capitulo_norm, presupuesto.building_type)

        if ratio_db is None or ratio_db.median is None:
            capitulos_sin_ratio.append(capitulo_norm)
            continue

        # Average value across items in this chapter (€/m²)
        valor_mio = (
            sum(i.valor_unitario * i.cantidad for i in items) / len(items)
        )
        valor_ratio = ratio_db.median
        desviacion_pct = (
            ((valor_mio - valor_ratio) / valor_ratio * 100) if valor_ratio else 0.0
        )
        impacto_monetario = (desviacion_pct / 100) * valor_ratio * presupuesto.area_total

        confiabilidad = calcular_estado_confiabilidad(ratio_db.sample_count)
        confiabilidades.append(confiabilidad)

        capitulos_resultado.append(
            ComparativaCapitulo(
                capitulo=capitulo_norm,
                descripcion=ratio_db.chapter_name,
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
        min(confiabilidades, key=lambda x: _CONFIABILIDAD_ORDEN.get(x, 0))
        if confiabilidades
        else "muy_debil"
    )

    diferencia_monetaria = total_presupuesto - total_ratio
    diferencia_pct = (
        (diferencia_monetaria / total_ratio * 100) if total_ratio else 0.0
    )

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


def _buscar_ratio(
    session: Session, chapter_code: str, building_type: Optional[str]
) -> Optional[Ratio]:
    """Find a Ratio row for a given chapter, preferring building_type match."""
    if building_type:
        ratio = (
            session.query(Ratio)
            .filter(
                func.upper(Ratio.chapter_code) == chapter_code,
                func.upper(Ratio.building_type) == building_type.upper(),
            )
            .first()
        )
        if ratio:
            return ratio
    # Fall back: any ratio for this chapter
    return (
        session.query(Ratio)
        .filter(func.upper(Ratio.chapter_code) == chapter_code)
        .first()
    )
