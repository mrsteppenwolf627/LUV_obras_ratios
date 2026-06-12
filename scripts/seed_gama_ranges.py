"""Seed script for gama_ranges table with base material definitions."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.db.schema import GamaRange, Base
from src.db.models import get_session


GAMA_RANGES_BASE = [
    {
        "material_type": "PORCELANA",
        "categoria": "REVESTIMIENTOS",
        "medium_min": 50.0,
        "medium_max": 100.0,
        "premium_min": 100.0,
        "premium_max": 200.0,
        "luxury_min": 200.0,
        "luxury_max": 400.0,
        "luxury_plus_min": 400.0,
        "luxury_plus_max": 800.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Azulejos y porcelánico estándar",
    },
    {
        "material_type": "PIEDRA",
        "categoria": "REVESTIMIENTOS",
        "medium_min": 80.0,
        "medium_max": 150.0,
        "premium_min": 150.0,
        "premium_max": 300.0,
        "luxury_min": 300.0,
        "luxury_max": 600.0,
        "luxury_plus_min": 600.0,
        "luxury_plus_max": 1200.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Piedra natural: mármol, granito, pizarra",
    },
    {
        "material_type": "PINTURA",
        "categoria": "ACABADOS",
        "medium_min": 5.0,
        "medium_max": 15.0,
        "premium_min": 15.0,
        "premium_max": 30.0,
        "luxury_min": 30.0,
        "luxury_max": 60.0,
        "luxury_plus_min": 60.0,
        "luxury_plus_max": 120.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Pintura estándar, anti-humedad, antimicrobiana",
    },
    {
        "material_type": "METAL",
        "categoria": "CARPINTERIA",
        "medium_min": 200.0,
        "medium_max": 400.0,
        "premium_min": 400.0,
        "premium_max": 800.0,
        "luxury_min": 800.0,
        "luxury_max": 1500.0,
        "luxury_plus_min": 1500.0,
        "luxury_plus_max": 3000.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Herrería, acero estructural, aluminio anodizado",
    },
    {
        "material_type": "VIDRIO",
        "categoria": "CERRAMIENTOS",
        "medium_min": 150.0,
        "medium_max": 300.0,
        "premium_min": 300.0,
        "premium_max": 600.0,
        "luxury_min": 600.0,
        "luxury_max": 1200.0,
        "luxury_plus_min": 1200.0,
        "luxury_plus_max": 2500.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Cristalería: simple, templado, laminado, Low-E",
    },
    {
        "material_type": "MADERA",
        "categoria": "CARPINTERIA",
        "medium_min": 100.0,
        "medium_max": 250.0,
        "premium_min": 250.0,
        "premium_max": 500.0,
        "luxury_min": 500.0,
        "luxury_max": 1000.0,
        "luxury_plus_min": 1000.0,
        "luxury_plus_max": 2500.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Madera: coníferas, frondosas, exóticas, acabados especiales",
    },
    {
        "material_type": "TEXTIL",
        "categoria": "ACABADOS",
        "medium_min": 30.0,
        "medium_max": 80.0,
        "premium_min": 80.0,
        "premium_max": 150.0,
        "luxury_min": 150.0,
        "luxury_max": 300.0,
        "luxury_plus_min": 300.0,
        "luxury_plus_max": 600.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Moqueta, tejidos, papel tapiz técnico",
    },
    {
        "material_type": "ENCIMERA",
        "categoria": "MOBILIARIO",
        "medium_min": 80.0,
        "medium_max": 200.0,
        "premium_min": 200.0,
        "premium_max": 400.0,
        "luxury_min": 400.0,
        "luxury_max": 800.0,
        "luxury_plus_min": 800.0,
        "luxury_plus_max": 1500.0,
        "fuente": "Libro de Gamas v1.0",
        "notas": "Madera, laminado, silestone, cuarzo, mármol",
    },
]


def seed_gama_ranges(session: Session | None = None) -> int:
    """
    Insert base gama_ranges data.
    Returns number of rows inserted.
    """
    if session is None:
        session = get_session()

    inserted = 0
    for data in GAMA_RANGES_BASE:
        existing = session.query(GamaRange).filter(
            GamaRange.material_type == data["material_type"],
            GamaRange.categoria == data["categoria"],
        ).first()

        if not existing:
            gama = GamaRange(**data)
            session.add(gama)
            inserted += 1

    session.commit()
    return inserted


if __name__ == "__main__":
    session = get_session()
    count = seed_gama_ranges(session)
    print(f"[OK] Inserted {count} gama_ranges records")
    session.close()
