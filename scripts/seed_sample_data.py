#!/usr/bin/env python3
"""Populate database with 36 sample items for testing."""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db.models import get_session
from src.db.schema import ItemMaster, ItemMasterRatio, Categoria, Confianza, Budget, LineItem


def seed_database() -> None:
    """Create 36 sample items with ratios."""
    session = get_session()

    try:
        # Create 3 sample budgets
        budgets = []
        for i in range(1, 4):
            budget = Budget(
                filename=f"presupuesto_{i:03d}.xlsx",
                file_hash=f"hash_{i:064d}",
                surface_m2=150.0 + i * 10,
                building_type="RESIDENTIAL",
                source_format="excel",
                total_cost=50000.0 + i * 5000,
            )
            session.add(budget)
            budgets.append(budget)

        session.flush()  # Get IDs
        print(f"✅ Created {len(budgets)} sample budgets")

        # Create 36 items
        categories = [
            ("Fundación", "Cimentación"),
            ("Estructura", "Hormigón"),
            ("Envolvente", "Fachada"),
            ("Cubierta", "Estructura"),
            ("Particiones", "Tabiquería"),
            ("Pavimentos", "Base"),
        ]

        sample_items = [
            ("Excavación", 50.0, "m3"),
            ("Hormigón armado pilares", 450.0, "m3"),
            ("Acero laminado estructural", 1200.0, "t"),
            ("Ladrillo cara vista", 0.12, "ud"),
            ("Bloque hormigón", 0.08, "ud"),
            ("Mortero cemento", 500.0, "kg"),
            ("Teja cerámica", 0.15, "ud"),
            ("Aislamiento térmico", 25.0, "m2"),
            ("Impermeabilización", 30.0, "m2"),
            ("Tabique yeso laminado", 12.0, "m2"),
            ("Puerta interior madera", 350.0, "ud"),
            ("Ventana aluminio doble acristalamiento", 280.0, "ud"),
            ("Pavimento gres porcelánico", 35.0, "m2"),
            ("Revestimiento azulejo", 20.0, "m2"),
            ("Tarima madera", 60.0, "m2"),
            ("Pintura interior acética", 8.0, "L"),
            ("Pintura exterior poliuretano", 12.0, "L"),
            ("Parquet flotante", 50.0, "m2"),
            ("Rodapié madera", 3.0, "m"),
            ("Moldura escayola", 2.0, "m"),
            ("Radiador acero", 250.0, "ud"),
            ("Bomba calor", 2000.0, "ud"),
            ("Tubo cobre calefacción", 15.0, "m"),
            ("Fontanería PVC", 8.0, "m"),
            ("Cableado eléctrico", 0.80, "m"),
            ("Enchufe base 16A", 12.0, "ud"),
            ("Interruptor simple", 8.0, "ud"),
            ("Luminaria LED", 120.0, "ud"),
            ("Puerta cortafuegos", 800.0, "ud"),
            ("Escalera interior", 2500.0, "ud"),
            ("Barandilla acero", 150.0, "m"),
            ("Ascensor residencial", 12000.0, "ud"),
            ("Antena parabólica", 400.0, "ud"),
            ("Puerta de acceso", 500.0, "ud"),
            ("Portero automático", 200.0, "ud"),
            ("Sistema seguridad CCTV", 1500.0, "ud"),
        ]

        items_created = 0
        for idx, (item_name, unit_price, unit) in enumerate(sample_items, 1):
            cat_idx = (idx - 1) % len(categories)
            cat_name, subcat_name = categories[cat_idx]

            item_key = f"{cat_name.lower()}_{item_name.lower().replace(' ', '_')}"
            item = ItemMaster(
                item_key=item_key,
                categoria=cat_name,
                subcategoria=subcat_name,
                unidad=unit,
                mediana_unitario=unit_price,
                media_unitario=unit_price * 1.05,
                min_unitario=unit_price * 0.85,
                max_unitario=unit_price * 1.25,
                desv_std=unit_price * 0.15,
                muestras_count=5,
                primera_fecha=datetime.now(timezone.utc),
                ultima_fecha=datetime.now(timezone.utc),
                categoria_asignada="MEDIUM" if idx % 3 == 0 else "PREMIUM" if idx % 3 == 1 else "LUXURY",
            )
            session.add(item)
            items_created += 1

        session.flush()
        print(f"✅ Created {items_created} sample items")

        # Create sample line items linked to budgets
        line_items_created = 0
        for budget_idx, budget in enumerate(budgets):
            for item_idx in range(12):  # 12 items per budget
                item_key = f"item_{budget_idx}_{item_idx}"
                price = 100.0 + (budget_idx * 20) + (item_idx * 10)

                line_item = LineItem(
                    budget_id=budget.id,
                    chapter_code=f"CH-{budget_idx:02d}-{item_idx:02d}",
                    chapter_name=f"Chapter {item_idx}",
                    description=f"Sample item {item_idx} for budget {budget_idx}",
                    quantity=1.0 + (item_idx * 0.5),
                    unit="ud",
                    unit_cost=price,
                    total_cost=price * (1.0 + (item_idx * 0.5)),
                    validation_status="VALID",
                )
                session.add(line_item)
                line_items_created += 1

        session.commit()
        print(f"✅ Created {line_items_created} sample line items")
        print(f"\n✅ Database seeded successfully!")
        print(f"   • 3 budgets")
        print(f"   • 36 item masters")
        print(f"   • {line_items_created} line items")

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
