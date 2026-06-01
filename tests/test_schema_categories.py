"""Tests for schema extensions: Categoria/Confianza enums, ItemMasterRatio, and new columns."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.schema import (
    Base,
    Budget,
    Categoria,
    Confianza,
    ItemInstance,
    ItemMaster,
    ItemMasterRatio,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_categoria_enum():
    assert Categoria.MEDIUM.value == "MEDIUM"
    assert Categoria.PREMIUM.value == "PREMIUM"
    assert Categoria.LUXURY.value == "LUXURY"
    assert Categoria.LUXURY_PLUS.value == "LUXURY_PLUS"


def test_confianza_enum():
    assert Confianza.MUY_DEBIL.value == "MUY_DÉBIL"
    assert Confianza.DEBIL.value == "DÉBIL"
    assert Confianza.SOLIDO.value == "SÓLIDO"
    assert Confianza.MUY_SOLIDO.value == "MUY_SÓLIDO"


def test_item_master_categoria_asignada(db_session):
    item = ItemMaster(item_key="carpinteria_001", categoria_asignada="PREMIUM")
    db_session.add(item)
    db_session.commit()

    assert item.id is not None
    assert item.categoria_asignada == "PREMIUM"


def test_item_master_categoria_default(db_session):
    item = ItemMaster(item_key="carpinteria_002")
    db_session.add(item)
    db_session.commit()

    assert item.categoria_asignada == "MEDIUM"


def test_item_master_ratio_creation(db_session):
    item = ItemMaster(item_key="carpinteria_003", categoria_asignada="PREMIUM")
    db_session.add(item)
    db_session.commit()

    ratio = ItemMasterRatio(
        item_master_id=item.id,
        categoria="PREMIUM",
        ratio_actual=250.0,
        mediana=245.0,
        min_valor=200.0,
        max_valor=300.0,
        desv_std=30.0,
        muestras_count=5,
        confianza="SÓLIDO",
    )
    db_session.add(ratio)
    db_session.commit()

    assert ratio.id is not None
    assert ratio.ratio_actual == 250.0
    assert ratio.muestras_count == 5
    assert ratio.confianza == "SÓLIDO"


def test_item_master_ratio_unique_constraint(db_session):
    item = ItemMaster(item_key="carpinteria_004", categoria_asignada="LUXURY")
    db_session.add(item)
    db_session.commit()

    db_session.add(ItemMasterRatio(item_master_id=item.id, categoria="LUXURY", ratio_actual=500.0, muestras_count=3))
    db_session.commit()

    db_session.add(ItemMasterRatio(item_master_id=item.id, categoria="LUXURY", ratio_actual=520.0, muestras_count=4))
    with pytest.raises(Exception):
        db_session.commit()


def test_item_master_ratio_relationship(db_session):
    item = ItemMaster(item_key="test_rel_001", categoria_asignada="MEDIUM")
    db_session.add(item)
    db_session.commit()

    for cat, ratio_val in [("MEDIUM", 200.0), ("PREMIUM", 350.0), ("LUXURY", 600.0)]:
        db_session.add(ItemMasterRatio(item_master_id=item.id, categoria=cat, ratio_actual=ratio_val, muestras_count=1))
    db_session.commit()

    db_session.refresh(item)
    assert len(item.ratios_por_categoria) == 3
    assert all(r.item_master_id == item.id for r in item.ratios_por_categoria)


def test_item_instance_new_columns(db_session):
    budget = Budget(filename="test.xlsx", file_hash="abc123", source_format="excel")
    db_session.add(budget)
    db_session.commit()

    item = ItemMaster(item_key="madera_001", categoria_asignada="LUXURY_PLUS")
    db_session.add(item)
    db_session.commit()

    instance = ItemInstance(
        budget_id=budget.id,
        item_master_id=item.id,
        categoria_asignada="LUXURY_PLUS",
        precio_unitario=750.0,
        ratio_comparativa=720.0,
    )
    db_session.add(instance)
    db_session.commit()

    assert instance.categoria_asignada == "LUXURY_PLUS"
    assert instance.ratio_comparativa == 720.0


def test_item_instance_categoria_default(db_session):
    budget = Budget(filename="test2.xlsx", file_hash="def456", source_format="excel")
    db_session.add(budget)
    db_session.commit()

    item = ItemMaster(item_key="madera_002")
    db_session.add(item)
    db_session.commit()

    instance = ItemInstance(budget_id=budget.id, item_master_id=item.id, precio_unitario=100.0)
    db_session.add(instance)
    db_session.commit()

    assert instance.categoria_asignada == "MEDIUM"
    assert instance.ratio_comparativa is None


def test_cascade_delete_ratios(db_session):
    item = ItemMaster(item_key="cascade_test_001", categoria_asignada="MEDIUM")
    db_session.add(item)
    db_session.commit()

    db_session.add(ItemMasterRatio(item_master_id=item.id, categoria="MEDIUM", ratio_actual=200.0, muestras_count=2))
    db_session.commit()

    db_session.delete(item)
    db_session.commit()

    remaining = db_session.query(ItemMasterRatio).filter_by(item_master_id=item.id).count()
    assert remaining == 0
