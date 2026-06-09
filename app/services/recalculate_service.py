"""Service to recalculate all ItemMaster statistics from ItemInstances."""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def recalculate_all_item_master_stats(session: Session) -> int:
    """
    Recalculate mediana_unitario and other stats for ALL ItemMaster items
    based on their ItemInstances.

    Returns: count of ItemMaster records updated
    """
    from src.db.schema import ItemMaster
    from src.ratios.item_ratio_calculator import recalculate_item_master_stats

    masters = session.query(ItemMaster).all()
    updated = 0

    for master in masters:
        if recalculate_item_master_stats(session, master.id):
            updated += 1

    session.flush()
    logger.info(f"Recalculated stats for {updated}/{len(masters)} ItemMaster items")
    return updated
