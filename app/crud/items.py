"""CRUD helpers for ItemMaster and ItemInstance."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session


def get_or_create_item_master(
    session: Session,
    item_key: str,
    categoria: Optional[str],
    subcategoria: Optional[str],
    unidad: Optional[str],
) -> "ItemMaster":  # type: ignore[name-defined]  # noqa: F821
    from src.db.schema import ItemMaster

    master = session.query(ItemMaster).filter(ItemMaster.item_key == item_key).first()
    if master is None:
        master = ItemMaster(
            item_key=item_key,
            categoria=categoria,
            subcategoria=subcategoria,
            unidad=unidad,
            muestras_count=0,
        )
        session.add(master)
        session.flush()
    return master


def search_items(
    session: Session,
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    from src.db.schema import ItemMaster

    query = session.query(ItemMaster)

    if q:
        query = query.filter(ItemMaster.item_key.ilike(f"%{q.lower()}%"))
    if categoria:
        query = query.filter(ItemMaster.categoria == categoria.upper())

    masters = query.order_by(ItemMaster.muestras_count.desc()).limit(limit).all()
    return [_master_to_dict(m) for m in masters]


def get_items_by_category(session: Session, categoria: str) -> list[dict]:
    from src.db.schema import ItemMaster

    masters = (
        session.query(ItemMaster)
        .filter(ItemMaster.categoria == categoria.upper())
        .order_by(ItemMaster.muestras_count.desc())
        .all()
    )
    return [_master_to_dict(m) for m in masters]


def get_item_history(session: Session, item_key: str) -> Optional[dict]:
    from src.db.schema import ItemInstance, ItemMaster

    master = session.query(ItemMaster).filter(ItemMaster.item_key == item_key).first()
    if not master:
        return None

    instances = (
        session.query(ItemInstance)
        .filter(ItemInstance.item_master_id == master.id)
        .order_by(ItemInstance.created_at)
        .all()
    )

    history = [
        {
            "presupuesto_id": i.budget_id,
            "codigo": i.codigo,
            "unidad": i.unidad or master.unidad or "",
            "cantidad": i.cantidad,
            "precio_unitario": i.precio_unitario,
            "precio_total": i.precio_total,
            "clasificacion_precio": i.clasificacion_precio,
            "desviacion_vs_historico": i.desviacion_vs_historico,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in instances
    ]

    prices = [i.precio_unitario for i in instances if i.precio_unitario and i.precio_unitario > 0]
    stats: dict = {}
    if prices:
        import statistics as _stats
        mediana = round(_stats.median(prices), 4)
        unidad_m = master.unidad or "ud"
        stats = {
            "mediana": mediana,
            "media": round(_stats.mean(prices), 4),
            "min": round(min(prices), 4),
            "max": round(max(prices), 4),
            "desv_std": round(_stats.stdev(prices), 4) if len(prices) > 1 else 0.0,
            "unidad": unidad_m,
            "unidad_medida": f"€/{unidad_m}",
            "tendencia": _tendencia(prices),
        }

    return {
        "item_key": master.item_key,
        "categoria": master.categoria,
        "subcategoria": master.subcategoria,
        "unidad": master.unidad,
        "history": history,
        "stats": stats,
    }


def _master_to_dict(m: "ItemMaster") -> dict:  # type: ignore[name-defined]  # noqa: F821
    unidad = m.unidad or "ud"
    return {
        "item_key": m.item_key,
        "categoria": m.categoria,
        "subcategoria": m.subcategoria,
        "unidad": unidad,
        "unidad_medida": f"€/{unidad}",
        "mediana_unitario": m.mediana_unitario,
        "media_unitario": m.media_unitario,
        "min_unitario": m.min_unitario,
        "max_unitario": m.max_unitario,
        "desv_std": m.desv_std,
        "muestras_count": m.muestras_count or 0,
        "primera_fecha": m.primera_fecha.isoformat() if m.primera_fecha else None,
        "ultima_fecha": m.ultima_fecha.isoformat() if m.ultima_fecha else None,
    }


def _tendencia(prices: list[float]) -> str:
    if len(prices) < 2:
        return "sin_datos"
    delta = prices[-1] - prices[0]
    pct = delta / prices[0] * 100 if prices[0] > 0 else 0
    if pct > 5:
        return "subiendo"
    if pct < -5:
        return "bajando"
    return "estable"
