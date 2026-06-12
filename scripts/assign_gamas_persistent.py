"""Script to assign and persist gama_asignada for all items in item_master."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.utils.gama_utils import determine_gama, find_gama_range
from src.db.models import get_session
from src.db.schema import ItemMaster


def assign_gamas_to_all_items(session: Session | None = None) -> dict:
    """
    Iterate all ItemMaster records and assign gama_asignada based on mediana_unitario.

    Returns:
        dict with counts: {
            'total_items': int,
            'with_gama_assigned': int,
            'sin_clasificar': int,
            'updated': list of (id, item_key, gama_assigned)
        }
    """
    if session is None:
        session = get_session()

    # Fetch all items
    items = session.query(ItemMaster).all()
    total_items = len(items)

    with_gama_assigned = 0
    sin_clasificar = 0
    updated: list[tuple[int, str, str]] = []

    for item in items:
        # Find gama_range matching item categoria
        gama_row = find_gama_range(session, item.categoria)

        # Determine gama tier based on median price
        gama_asignada = determine_gama(item.mediana_unitario, gama_row)

        # Update item
        item.gama_asignada = gama_asignada
        updated.append((item.id, item.item_key, gama_asignada))

        if gama_asignada == "SIN_CLASIFICAR":
            sin_clasificar += 1
        else:
            with_gama_assigned += 1

    # Commit changes
    session.commit()

    return {
        "total_items": total_items,
        "with_gama_assigned": with_gama_assigned,
        "sin_clasificar": sin_clasificar,
        "updated": updated,
    }


if __name__ == "__main__":
    print("Assigning gamas to all items...")
    session = get_session()
    result = assign_gamas_to_all_items(session)
    session.close()

    print()
    print(f"Total items: {result['total_items']}")
    print(f"With gama assigned: {result['with_gama_assigned']}")
    print(f"Sin clasificar: {result['sin_clasificar']}")
    print()
    print(f"Updated {len(result['updated'])} items:")
    for item_id, item_key, gama in result["updated"][:10]:
        print(f"  {item_id:3d} | {item_key:50s} | {gama}")
    if len(result["updated"]) > 10:
        print(f"  ... and {len(result['updated']) - 10} more")
