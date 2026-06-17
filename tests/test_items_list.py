"""Tests for GET /api/items/list (ported to the serverless router)."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from src.db.schema import Base, ItemMaster
from app import database as db_module
from app import main as app_module
from app.routers import items_extended as items_extended_module


def _make_client(seed=None):
    """Build a TestClient backed by a fresh in-memory DB, optionally seeded."""
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

    if seed is not None:
        session = _Session()
        seed(session)
        session.commit()
        session.close()

    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db
    items_extended_module._db.get_db = _fake_get_db

    client = TestClient(app_module.app)
    return client, original_get_db


@pytest.fixture
def empty_client():
    client, original_get_db = _make_client()
    yield client
    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    items_extended_module._db.get_db = original_get_db


@pytest.fixture
def populated_client():
    def seed(session):
        session.add_all([
            ItemMaster(
                item_key="vigas_metalicas",
                categoria="ESTRUCTURA",
                categoria_asignada="ESTRUCTURA",
                muestras_count=3,
            ),
            ItemMaster(
                item_key="griferia_bano",
                categoria="FONTANERIA",
                categoria_asignada="FONTANERIA",
                muestras_count=1,
            ),
        ])

    client, original_get_db = _make_client(seed)
    yield client
    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    items_extended_module._db.get_db = original_get_db


class TestItemsList:
    def test_empty_db_returns_empty_list(self, empty_client):
        resp = empty_client.get("/api/items/list")
        assert resp.status_code == 200
        assert resp.json() == {"items": []}

    def test_returns_items(self, populated_client):
        resp = populated_client.get("/api/items/list")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        # Ordered by item_key asc: griferia_bano before vigas_metalicas
        assert items[0]["item_key"] == "griferia_bano"
        assert items[1]["item_key"] == "vigas_metalicas"
        # Shape: ratio is None (outerjoin with no ItemMasterRatio rows)
        first = items[0]
        assert set(first.keys()) == {
            "id", "item_key", "descripcion", "categoria_asignada",
            "muestras_count", "ratio_actual", "confianza",
        }
        assert first["descripcion"] == "Griferia Bano"
        assert first["ratio_actual"] is None
        assert first["confianza"] is None

    def test_filter_by_categoria(self, populated_client):
        resp = populated_client.get("/api/items/list?categoria=fontaneria")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["categoria_asignada"] == "FONTANERIA"
