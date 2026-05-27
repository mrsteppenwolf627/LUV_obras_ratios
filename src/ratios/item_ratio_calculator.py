"""Historical ratio statistics and price alert classification for individual items."""

from __future__ import annotations

import statistics
from typing import Optional


# Deviation thresholds (percentage)
_ANOMALY_LOW = -30.0
_CHEAP_THRESHOLD = -15.0
_EXPENSIVE_THRESHOLD = 15.0
_ANOMALY_HIGH = 30.0

# Sample sizes for confidence tiers
_HIGH_CONF_N = 5
_MED_CONF_N = 3


def get_item_ratio_history(session, item_master_id: int) -> Optional[dict]:
    """
    Compute price statistics for an ItemMaster from its ItemInstances.

    Returns None if there are no priced instances.
    """
    from src.db.schema import ItemInstance, ItemMaster

    master = session.get(ItemMaster, item_master_id)
    unidad = (master.unidad or "") if master else ""

    instances = (
        session.query(ItemInstance)
        .filter(ItemInstance.item_master_id == item_master_id)
        .order_by(ItemInstance.created_at)
        .all()
    )

    prices = [
        i.precio_unitario
        for i in instances
        if i.precio_unitario is not None and i.precio_unitario > 0
    ]

    if not prices:
        return None

    mediana = round(statistics.median(prices), 4)
    media = round(statistics.mean(prices), 4)
    min_val = round(min(prices), 4)
    max_val = round(max(prices), 4)
    desv_std = round(statistics.stdev(prices), 4) if len(prices) > 1 else 0.0
    desv_pct = round(desv_std / mediana * 100, 2) if mediana > 0 else 0.0

    samples = [
        {
            "presupuesto_id": i.budget_id,
            "precio_unitario": i.precio_unitario,
            "unidad": i.unidad or unidad,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in instances
        if i.precio_unitario is not None and i.precio_unitario > 0
    ]

    return {
        "muestras_count": len(prices),
        "mediana": mediana,
        "media": media,
        "min": min_val,
        "max": max_val,
        "desv_std": desv_std,
        "desv_porcentaje": desv_pct,
        "unidad": unidad,
        "muestras": samples,
    }


def compute_stats(prices: list[float]) -> dict:
    """
    Compute summary statistics from a list of prices.

    Utility for tests and callers that don't have a DB session.
    """
    if not prices:
        return {}
    valid = [p for p in prices if p is not None and p > 0]
    if not valid:
        return {}
    mediana = round(statistics.median(valid), 4)
    return {
        "muestras_count": len(valid),
        "mediana": mediana,
        "media": round(statistics.mean(valid), 4),
        "min": round(min(valid), 4),
        "max": round(max(valid), 4),
        "desv_std": round(statistics.stdev(valid), 4) if len(valid) > 1 else 0.0,
        "desv_porcentaje": (
            round(statistics.stdev(valid) / mediana * 100, 2)
            if len(valid) > 1 and mediana > 0
            else 0.0
        ),
    }


def classify_new_item_price(item: dict, historic_stats: Optional[dict]) -> dict:
    """
    Compare a new item's price against the historical median.

    Returns:
    {
        "clasificacion": PRIMERA_MUESTRA | SIN_PRECIO | BARATO | NORMAL | CARO | ANOMALÍA,
        "precio_nuevo": float | None,
        "precio_historico": float | None,
        "desviacion_absoluta": float,
        "desviacion_porcentaje": float,
        "confianza": BAJA | MEDIA | ALTA,
        "n_muestras": int,
        "accion": str,
    }
    """
    precio_nuevo = item.get("precio_unitario")

    unidad_item = item.get("unidad", "")
    unidad_hist = (historic_stats or {}).get("unidad", "")

    if precio_nuevo is None or precio_nuevo <= 0:
        return {
            "clasificacion": "SIN_PRECIO",
            "precio_nuevo": precio_nuevo,
            "precio_historico": None,
            "desviacion_absoluta": 0.0,
            "desviacion_porcentaje": 0.0,
            "confianza": "BAJA",
            "n_muestras": 0,
            "unidad": unidad_item,
            "accion": "Ítem sin precio unitario — marcar como DUBIOUS",
        }

    n = (historic_stats or {}).get("muestras_count", 0)
    if not historic_stats or n == 0:
        return {
            "clasificacion": "PRIMERA_MUESTRA",
            "precio_nuevo": precio_nuevo,
            "precio_historico": None,
            "desviacion_absoluta": 0.0,
            "desviacion_porcentaje": 0.0,
            "confianza": "BAJA",
            "n_muestras": 0,
            "unidad": unidad_item,
            "accion": "Primera muestra de este ítem — sin histórico disponible",
        }

    # Reject comparison when units differ (would mix e.g. €/m³ with €/kg)
    if unidad_hist and unidad_item and unidad_hist.lower() != unidad_item.lower():
        return {
            "clasificacion": "UNIDAD_DIFERENTE",
            "precio_nuevo": precio_nuevo,
            "precio_historico": historic_stats.get("mediana"),
            "desviacion_absoluta": 0.0,
            "desviacion_porcentaje": 0.0,
            "confianza": "BAJA",
            "n_muestras": n,
            "unidad": unidad_item,
            "accion": (
                f"Histórico en '{unidad_hist}', ítem nuevo en '{unidad_item}' "
                "— no comparables"
            ),
        }

    mediana = historic_stats["mediana"]
    if mediana <= 0:
        return {
            "clasificacion": "PRIMERA_MUESTRA",
            "precio_nuevo": precio_nuevo,
            "precio_historico": mediana,
            "desviacion_absoluta": 0.0,
            "desviacion_porcentaje": 0.0,
            "confianza": "BAJA",
            "n_muestras": n,
            "unidad": unidad_item,
            "accion": "Histórico con mediana ≤ 0, no comparable",
        }

    desv_abs = round(precio_nuevo - mediana, 4)
    desv_pct = round((precio_nuevo - mediana) / mediana * 100, 2)

    confianza = "ALTA" if n >= _HIGH_CONF_N else ("MEDIA" if n >= _MED_CONF_N else "BAJA")

    if desv_pct <= _ANOMALY_LOW:
        clasificacion = "ANOMALÍA"
        accion = (
            f"Precio {abs(desv_pct):.1f}% por debajo del histórico "
            "— posible error o alcance incompleto"
        )
    elif desv_pct < _CHEAP_THRESHOLD:
        clasificacion = "BARATO"
        accion = (
            f"Precio {abs(desv_pct):.1f}% por debajo del histórico "
            "— revisar si incluye todo el alcance"
        )
    elif desv_pct >= _ANOMALY_HIGH:
        clasificacion = "ANOMALÍA"
        accion = (
            f"Precio {desv_pct:.1f}% por encima del histórico "
            "— verificar con presupuestista"
        )
    elif desv_pct > _EXPENSIVE_THRESHOLD:
        clasificacion = "CARO"
        accion = f"Precio {desv_pct:.1f}% sobre histórico — revisar presupuestista"
    else:
        clasificacion = "NORMAL"
        accion = "Precio dentro del rango histórico normal"

    return {
        "clasificacion": clasificacion,
        "precio_nuevo": precio_nuevo,
        "precio_historico": mediana,
        "desviacion_absoluta": desv_abs,
        "desviacion_porcentaje": desv_pct,
        "confianza": confianza,
        "n_muestras": n,
        "unidad": unidad_item,
        "accion": accion,
    }


def recalculate_item_master_stats(session, item_master_id: int) -> bool:
    """
    Recompute ItemMaster aggregate columns from its ItemInstances and persist.

    Returns True if stats were updated, False if no data found.
    """
    from datetime import datetime, timezone
    from src.db.schema import ItemInstance, ItemMaster

    master = session.get(ItemMaster, item_master_id)
    if not master:
        return False

    stats = get_item_ratio_history(session, item_master_id)
    if not stats:
        return False

    master.mediana_unitario = stats["mediana"]
    master.media_unitario = stats["media"]
    master.min_unitario = stats["min"]
    master.max_unitario = stats["max"]
    master.desv_std = stats["desv_std"]
    master.muestras_count = stats["muestras_count"]
    master.ultima_actualizacion = datetime.now(timezone.utc)

    instances = (
        session.query(ItemInstance)
        .filter(ItemInstance.item_master_id == item_master_id)
        .all()
    )
    dates = [i.created_at for i in instances if i.created_at]
    if dates:
        master.primera_fecha = min(dates)
        master.ultima_fecha = max(dates)

    return True
