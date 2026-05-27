"""Space-level ratio calculator for Presto budgets (Hito 3).

Input: output of src.core.presto_reader.parse_presto()
Output: per-space ratios with optional plant breakdown and proration.
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_space_ratios(
    presupuesto: dict,
    areas: Optional[dict] = None,
) -> dict:
    """
    Calculate €/m² ratios per space.

    Args:
        presupuesto: output of parse_presto() — must contain "espacios" list.
        areas: optional m² mapping.
            Accepted formats:
              {space_name: {"PS": m2, "PB": m2, "PP": m2}}   — per-plant
              {space_name: total_m2_float}                    — aggregate only

    Returns:
        {
            "filename": str,
            "budget_code": str,
            "total_coste": float,
            "total_m2": float,
            "espacios": [
                {
                    "nombre": str,
                    "zona": str,
                    "plantas": {
                        "PS": {"m2": float, "coste": float, "ratio": float | None},
                        "PB": {...},
                        "PP": {...},
                    },
                    "total": {
                        "m2": float,
                        "coste": float,
                        "pct_m2": float,
                        "coste_prorrateado": float,
                        "ratio": float | None,
                        "ratio_prorrateado": float | None,
                    },
                }
            ],
        }
    """
    areas = areas or {}
    espacios_out = []
    total_m2_all = 0.0
    total_coste = presupuesto.get("total_coste", 0.0)

    for spc in presupuesto.get("espacios", []):
        nombre = spc["nombre"]
        coste_total = spc.get("coste", 0.0)
        zona = spc.get("zona", "COMUNES")

        m2_ps, m2_pb, m2_pp = _resolve_m2(nombre, areas, spc.get("m2", 0.0))
        m2_total = m2_ps + m2_pb + m2_pp
        total_m2_all += m2_total

        coste_ps, coste_pb, coste_pp = _split_cost(coste_total, m2_ps, m2_pb, m2_pp, m2_total)

        espacios_out.append(
            {
                "nombre": nombre,
                "zona": zona,
                "plantas": {
                    "PS": _plant_entry(m2_ps, coste_ps),
                    "PB": _plant_entry(m2_pb, coste_pb),
                    "PP": _plant_entry(m2_pp, coste_pp),
                },
                "total": {
                    "m2": round(m2_total, 4),
                    "coste": round(coste_total, 2),
                    "ratio": _safe_ratio(coste_total, m2_total),
                    # proration fields filled in second pass
                    "pct_m2": 0.0,
                    "coste_prorrateado": round(coste_total, 2),
                    "ratio_prorrateado": None,
                },
            }
        )

    # Second pass: proration (needs total_m2_all)
    for spc in espacios_out:
        m2_spc = spc["total"]["m2"]
        if total_m2_all > 0:
            pct = round(m2_spc / total_m2_all * 100, 4)
            coste_pro = round(m2_spc / total_m2_all * total_coste, 2)
        else:
            pct = 0.0
            coste_pro = spc["total"]["coste"]
        spc["total"]["pct_m2"] = pct
        spc["total"]["coste_prorrateado"] = coste_pro
        spc["total"]["ratio_prorrateado"] = _safe_ratio(coste_pro, m2_spc)

    return {
        "filename": presupuesto.get("filename", ""),
        "budget_code": presupuesto.get("budget_code", ""),
        "total_coste": round(total_coste, 2),
        "total_m2": round(total_m2_all, 4),
        "espacios": espacios_out,
    }


def calculate_proration(espacios: list, total_coste: float) -> list:
    """
    Prorratea total_coste among espacios based on m² distribution.

    Args:
        espacios: list of {"nombre": str, "m2": float, "coste": float}
        total_coste: global budget total

    Returns:
        same list enriched with "pct_m2" and "coste_prorrateado".
    """
    total_m2 = sum(float(e.get("m2", 0)) for e in espacios)
    for e in espacios:
        m2 = float(e.get("m2", 0))
        if total_m2 > 0:
            e["pct_m2"] = round(m2 / total_m2 * 100, 4)
            e["coste_prorrateado"] = round(m2 / total_m2 * total_coste, 2)
        else:
            e["pct_m2"] = 0.0
            e["coste_prorrateado"] = e.get("coste", 0.0)
        e["ratio"] = _safe_ratio(e["coste_prorrateado"], m2)
    return espacios


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_m2(
    nombre: str,
    areas: dict,
    fallback: float,
) -> tuple[float, float, float]:
    """Return (m2_PS, m2_PB, m2_PP) from areas dict or fallback."""
    if nombre not in areas:
        return fallback, 0.0, 0.0
    val = areas[nombre]
    if isinstance(val, dict):
        return (
            float(val.get("PS", 0.0)),
            float(val.get("PB", 0.0)),
            float(val.get("PP", 0.0)),
        )
    total = float(val)
    return total, 0.0, 0.0


def _split_cost(
    coste_total: float,
    m2_ps: float,
    m2_pb: float,
    m2_pp: float,
    m2_total: float,
) -> tuple[float, float, float]:
    """Distribute total cost proportionally to m² per plant."""
    if m2_total <= 0:
        return 0.0, 0.0, 0.0
    return (
        round(coste_total * m2_ps / m2_total, 2),
        round(coste_total * m2_pb / m2_total, 2),
        round(coste_total * m2_pp / m2_total, 2),
    )


def _plant_entry(m2: float, coste: float) -> dict:
    return {
        "m2": round(m2, 4),
        "coste": round(coste, 2),
        "ratio": _safe_ratio(coste, m2),
    }


def _safe_ratio(coste: float, m2: float) -> Optional[float]:
    if m2 and m2 > 0:
        return round(coste / m2, 2)
    return None
