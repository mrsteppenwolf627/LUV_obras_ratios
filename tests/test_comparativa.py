"""Tests for POST /api/analyze/comparativa endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from src.db.schema import Base, ItemMaster, ItemInstance, Budget
from app import database as db_module
from app import main as app_module


@pytest.fixture(scope="module")
def comparativa_client():
    """TestClient with ItemMaster, ItemInstance, and Budget test data."""
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

    # Budget padre
    budget = Budget(
        filename="test.xlsx",
        file_hash="t" * 64,
        source_format="excel",
        building_type="residential",
    )
    session.add(budget)
    session.flush()

    # ItemMaster para ESTRUCTURA (3 items)
    estructura_items = [
        ItemMaster(item_key="vigas metalicas estructura", categoria="ESTRUCTURA", unidad="m"),
        ItemMaster(item_key="forjado hormigon estructura", categoria="ESTRUCTURA", unidad="m2"),
        ItemMaster(item_key="pilares metalicos estructura", categoria="ESTRUCTURA", unidad="u"),
    ]
    for item in estructura_items:
        session.add(item)
    session.flush()

    # ItemMaster para PINTURA (2 items)
    pintura_items = [
        ItemMaster(item_key="pintura interior pintura", categoria="PINTURA", unidad="m2"),
        ItemMaster(item_key="pintura exterior pintura", categoria="PINTURA", unidad="m2"),
    ]
    for item in pintura_items:
        session.add(item)
    session.flush()

    # Crear ItemInstances para ESTRUCTURA
    # Item 0: 100, 120, 140 → mediana=120
    for precio in [100, 120, 140]:
        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=estructura_items[0].id,
            descripcion="Viga test",
            unidad="m",
            cantidad=1,
            precio_unitario=precio,
            precio_total=precio,
            validation_status="VALID",
        )
        session.add(inst)

    # Item 1: 200, 220, 240 → mediana=220
    for precio in [200, 220, 240]:
        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=estructura_items[1].id,
            descripcion="Forjado test",
            unidad="m2",
            cantidad=1,
            precio_unitario=precio,
            precio_total=precio,
            validation_status="VALID",
        )
        session.add(inst)

    # Crear ItemInstances para PINTURA
    # Item 0: 50, 60 → mediana=55
    for precio in [50, 60]:
        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=pintura_items[0].id,
            descripcion="Pintura interior",
            unidad="m2",
            cantidad=1,
            precio_unitario=precio,
            precio_total=precio,
            validation_status="VALID",
        )
        session.add(inst)

    session.commit()
    session.close()

    # Recalculate stats
    from app.services.recalculate_service import recalculate_all_item_master_stats
    session = _Session()
    recalculate_all_item_master_stats(session)
    session.commit()
    session.close()

    # Patch database
    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db


class TestComparativaEndpoint:
    def test_returns_200(self, comparativa_client):
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 150, "cantidad": 1, "unidad": "m2"}
                ],
            },
        )
        assert resp.status_code == 200

    def test_returns_comparativa_response_structure(self, comparativa_client):
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 150, "cantidad": 1, "unidad": "m2"}
                ],
            },
        )
        data = resp.json()

        # Check top-level keys
        assert "capitulos" in data
        assert "capitulos_sin_ratio" in data
        assert "resumen" in data

        # Check capitulos structure
        assert isinstance(data["capitulos"], list)
        if data["capitulos"]:
            cap = data["capitulos"][0]
            assert "capitulo" in cap
            assert "valor_mio" in cap
            assert "valor_ratio" in cap
            assert "desviacion_pct" in cap
            assert "impacto_monetario" in cap
            assert "estado_confiabilidad" in cap

        # Check resumen structure
        resumen = data["resumen"]
        assert "total_presupuesto" in resumen
        assert "total_ratio" in resumen
        assert "diferencia_pct" in resumen
        assert "diferencia_monetaria" in resumen
        assert "area_total" in resumen
        assert "confiabilidad_global" in resumen

    def test_calculates_deviation_correctly(self, comparativa_client):
        """Test deviation calculation: valor_mio=150, valor_ratio=120 → 25% desv."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 150, "cantidad": 1, "unidad": "m"}
                ],
            },
        )
        data = resp.json()

        # Should have 1 capitulo with data
        assert len(data["capitulos"]) >= 1
        cap = data["capitulos"][0]

        # Deviation: (150 - 120) / 120 * 100 = 25%
        assert cap["valor_mio"] == 150.0
        assert cap["valor_ratio"] == 120.0
        assert abs(cap["desviacion_pct"] - 25.0) < 1.0

    def test_multiple_items_same_chapter(self, comparativa_client):
        """Test when multiple items belong to same chapter (promedia)."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 100, "cantidad": 1, "unidad": "m"},
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 200, "cantidad": 1, "unidad": "m2"},
                ],
            },
        )
        data = resp.json()

        # Items en ESTRUCTURA: (100 + 200) / 2 = 150 promedio
        cap = [c for c in data["capitulos"] if c["capitulo"] == "ESTRUCTURA"]
        assert len(cap) == 1
        assert cap[0]["valor_mio"] == 150.0  # Average of 100 and 200

    def test_missing_chapter_goes_to_capitulos_sin_ratio(self, comparativa_client):
        """Test chapter with no ratio goes to capitulos_sin_ratio."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "INEXISTENTE", "valor_unitario": 100, "cantidad": 1, "unidad": "m2"}
                ],
            },
        )
        data = resp.json()

        # Should have 0 capitulos and 1 sin_ratio
        assert len(data["capitulos"]) == 0
        assert "INEXISTENTE" in data["capitulos_sin_ratio"]

    def test_area_total_zero_returns_422(self, comparativa_client):
        """Test that area_total=0 returns 422 validation error."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 0,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 150, "cantidad": 1, "unidad": "m2"}
                ],
            },
        )
        assert resp.status_code == 422

    def test_empty_items_list_returns_422(self, comparativa_client):
        """Test with empty items list - should return validation error."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [],
            },
        )
        # Pydantic validates empty list
        assert resp.status_code == 422

    def test_confiabilidad_based_on_muestras(self, comparativa_client):
        """Test confidence level depends on sample count."""
        resp = comparativa_client.post(
            "/api/analyze/comparativa",
            json={
                "area_total": 100,
                "items": [
                    {"capitulo": "ESTRUCTURA", "valor_unitario": 150, "cantidad": 1, "unidad": "m"}
                ],
            },
        )
        data = resp.json()

        cap = data["capitulos"][0]
        # ESTRUCTURA has 3 muestras (debil: 2-4)
        assert cap["estado_confiabilidad"] == "debil"
