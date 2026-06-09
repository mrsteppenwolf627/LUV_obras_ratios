"""Tests for GET /api/ratios/rango endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from src.db.schema import Base, ItemMaster, ItemInstance, Budget
from app import database as db_module
from app import main as app_module
from app.routers import stats as stats_module


@pytest.fixture(scope="module")
def stats_client():
    """TestClient with ItemMaster and ItemInstance test data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    _Session = sessionmaker(bind=engine)

    # Crear datos de prueba
    session = _Session()

    # Budget padre (requerido por FK)
    budget = Budget(
        filename="test.xlsx",
        file_hash="t" * 64,
        source_format="excel",
        building_type="residential",
    )
    session.add(budget)
    session.flush()

    # ItemMaster para ESTRUCTURA (6 items, 12 muestras)
    estructura_items = [
        ItemMaster(item_key="vigas metalicas estructura", categoria="ESTRUCTURA", unidad="m"),
        ItemMaster(item_key="forjado hormigon estructura", categoria="ESTRUCTURA", unidad="m2"),
        ItemMaster(item_key="pilares metalicos estructura", categoria="ESTRUCTURA", unidad="u"),
        ItemMaster(item_key="apuntalamiento estructura", categoria="ESTRUCTURA", unidad="m"),
        ItemMaster(item_key="reparacion grietas estructura", categoria="ESTRUCTURA", unidad="m2"),
        ItemMaster(item_key="andamiaje temporal estructura", categoria="ESTRUCTURA", unidad="m2"),
    ]
    for item in estructura_items:
        session.add(item)
    session.flush()

    # ItemMaster para FONTANERIA (3 items)
    fontaneria_items = [
        ItemMaster(item_key="tuberias pvc fontaneria", categoria="FONTANERIA", unidad="m"),
        ItemMaster(item_key="griferia bano fontaneria", categoria="FONTANERIA", unidad="u"),
        ItemMaster(item_key="inodoro fontaneria", categoria="FONTANERIA", unidad="u"),
    ]
    for item in fontaneria_items:
        session.add(item)
    session.flush()

    # Crear instances para ESTRUCTURA con precios específicos
    estructura_precios = [100, 150, 120, 180, 200, 160, 140, 170, 190, 175, 165, 155]
    for i, precio in enumerate(estructura_precios):
        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=estructura_items[i % 6].id,
            descripcion=f"Descripción {i}",
            unidad="m",
            cantidad=1,
            precio_unitario=precio,
            precio_total=precio,
            validation_status="VALID",
        )
        session.add(inst)

    # Crear instances para FONTANERIA con precios
    fontaneria_precios = [50, 75, 60]
    for i, precio in enumerate(fontaneria_precios):
        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=fontaneria_items[i].id,
            descripcion=f"Fontaneria {i}",
            unidad="u",
            cantidad=1,
            precio_unitario=precio,
            precio_total=precio,
            validation_status="VALID",
        )
        session.add(inst)

    session.commit()
    session.close()

    # Patch database
    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db
    stats_module._db.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    stats_module._db.get_db = original_get_db


class TestRatiosRango:
    def test_returns_200(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=ESTRUCTURA")
        assert resp.status_code == 200

    def test_has_required_fields(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=ESTRUCTURA")
        data = resp.json()
        required_fields = {
            "chapter", "items_count", "muestras_total",
            "min_unitario", "max_unitario", "p25_unitario",
            "median_unitario", "p75_unitario", "avg_unitario"
        }
        assert set(data.keys()) == required_fields

    def test_estructura_data_correct(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=ESTRUCTURA")
        data = resp.json()

        # Verificar valores específicos
        assert data["chapter"] == "ESTRUCTURA"
        assert data["items_count"] == 6
        assert data["muestras_total"] == 12
        assert data["min_unitario"] == 100.0
        assert data["max_unitario"] == 200.0
        # Precios ordenados: [100, 120, 140, 150, 155, 160, 165, 170, 175, 180, 190, 200]
        # Mediana es promedio de posiciones 5 y 6 (0-indexed): (160+165)/2 = 162.5
        assert abs(data["median_unitario"] - 162.5) < 0.1
        # Promedio: (100+150+120+180+200+160+140+170+190+175+165+155)/12 = 158.75
        assert abs(data["avg_unitario"] - 158.75) < 0.1

    def test_fontaneria_data(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=FONTANERIA")
        data = resp.json()

        assert data["chapter"] == "FONTANERIA"
        assert data["items_count"] == 3
        assert data["muestras_total"] == 3
        assert data["min_unitario"] == 50.0
        assert data["max_unitario"] == 75.0

    def test_missing_chapter_param(self, stats_client):
        resp = stats_client.get("/api/ratios/rango")
        assert resp.status_code == 400

    def test_nonexistent_chapter(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=INEXISTENTE")
        assert resp.status_code == 404

    def test_case_insensitive_chapter(self, stats_client):
        resp = stats_client.get("/api/ratios/rango?chapter=estructura")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chapter"] == "ESTRUCTURA"
