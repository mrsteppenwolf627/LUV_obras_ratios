"""Script to assign and persist gama_asignada for all items in item_master."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.utils.gama_utils import determine_gama, find_gama_range
from src.db.models import get_session
from src.db.schema import ItemMaster

logger = logging.getLogger(__name__)


def assign_gamas_to_all_items(session: Session | None = None) -> dict:
    """
    Iterate all ItemMaster records and assign gama_asignada based on mediana_unitario.

    Returns:
        dict with counts: {
            'total_items': int,
            'with_gama_assigned': int,
            'sin_clasificar': int,
            'updated': list of (id, item_key, gama_assigned),
            'errors': list of (id, item_key, error_msg)
        }
    """
    should_close_session = False
    if session is None:
        session = get_session()
        should_close_session = True

    with_gama_assigned = 0
    sin_clasificar = 0
    updated: list[tuple[int, str, str]] = []
    errors: list[tuple[int, str, str]] = []

    try:
        # Fetch all items
        items = session.query(ItemMaster).all()
        total_items = len(items)
        logger.info(f"Starting gama assignment for {total_items} items")

        for idx, item in enumerate(items, start=1):
            try:
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

                # Log progress every 50 items
                if idx % 50 == 0:
                    logger.debug(f"Processed {idx}/{total_items} items")

            except Exception as item_error:
                error_msg = f"{type(item_error).__name__}: {str(item_error)}"
                logger.error(f"Error processing item {item.id} ({item.item_key}): {error_msg}")
                errors.append((item.id, item.item_key, error_msg))
                session.rollback()

        # Commit changes only if no errors
        if not errors:
            session.commit()
            logger.info(
                f"Successfully assigned gamas: {with_gama_assigned} assigned, "
                f"{sin_clasificar} sin_clasificar"
            )
        else:
            session.rollback()
            logger.error(f"Failed to assign gamas due to {len(errors)} item(s) error(s)")

        return {
            "total_items": total_items,
            "with_gama_assigned": with_gama_assigned,
            "sin_clasificar": sin_clasificar,
            "updated": updated,
            "errors": errors,
        }

    except Exception as global_error:
        error_msg = f"{type(global_error).__name__}: {str(global_error)}"
        logger.error(f"Critical error in assign_gamas_to_all_items: {error_msg}")
        session.rollback()
        return {
            "total_items": 0,
            "with_gama_assigned": 0,
            "sin_clasificar": 0,
            "updated": updated,
            "errors": [(None, None, error_msg)],
        }

    finally:
        if should_close_session:
            session.close()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    print("[*] Assigning gamas to all items...")
    result = assign_gamas_to_all_items()

    print()
    print(f"[RESULTS]")
    print(f"  Total items: {result['total_items']}")
    print(f"  With gama assigned: {result['with_gama_assigned']}")
    print(f"  Sin clasificar: {result['sin_clasificar']}")
    print(f"  Errors: {len(result['errors'])}")

    if result["errors"]:
        print()
        print("[ERRORS]")
        for item_id, item_key, error_msg in result["errors"][:5]:
            print(f"  {item_id} | {item_key} | {error_msg}")
        if len(result["errors"]) > 5:
            print(f"  ... and {len(result['errors']) - 5} more")

    if result["updated"]:
        print()
        print(f"[UPDATED ITEMS] {len(result['updated'])} items:")
        for item_id, item_key, gama in result["updated"][:10]:
            print(f"  {item_id:3d} | {item_key:50s} | {gama}")
        if len(result["updated"]) > 10:
            print(f"  ... and {len(result['updated']) - 10} more")

    print()
    if result["errors"]:
        print("[EXIT] Failed - see errors above")
        sys.exit(1)
    else:
        print("[OK] All items processed successfully")
        sys.exit(0)
