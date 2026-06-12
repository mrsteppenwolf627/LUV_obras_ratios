from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.gama_utils import determine_gama, find_gama_range
from src.db.schema import Base, GamaRange, ItemMaster


def _build_gama_range(
    categoria: str,
    *,
    medium: tuple[float, float],
    premium: tuple[float, float],
    luxury: tuple[float, float],
    luxury_plus: tuple[float, float],
) -> GamaRange:
    return GamaRange(
        material_type=categoria,
        categoria=categoria,
        medium_min=medium[0],
        medium_max=medium[1],
        premium_min=premium[0],
        premium_max=premium[1],
        luxury_min=luxury[0],
        luxury_max=luxury[1],
        luxury_plus_min=luxury_plus[0],
        luxury_plus_max=luxury_plus[1],
        fuente="test",
    )


@pytest.fixture(scope="module")
def api_client():
    from app import database as db_module
    from app import main as app_module
    from app.routers import items_extended as items_extended_module

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    original_db_get = db_module.get_db
    original_app_get = app_module.get_db
    original_router_get = items_extended_module._db.get_db

    def _fake_get_db():
        return SessionLocal()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db
    items_extended_module._db.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client, SessionLocal

    db_module.get_db = original_db_get
    app_module.get_db = original_app_get
    items_extended_module._db.get_db = original_router_get


@pytest.fixture
def client_and_session(api_client):
    return api_client


def test_assign_gama_unitario_25_porcelana_returns_premium(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()
    gama_range = _build_gama_range(
        "PORCELANA",
        medium=(0, 19.99),
        premium=(20, 49.99),
        luxury=(50, 99.99),
        luxury_plus=(100, 199.99),
    )

    assert determine_gama(25, gama_range) == "PREMIUM"
    session.close()


def test_assign_gama_unitario_150_piedra_returns_luxury(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()
    gama_range = _build_gama_range(
        "PIEDRA",
        medium=(0, 49.99),
        premium=(50, 99.99),
        luxury=(100, 199.99),
        luxury_plus=(200, 399.99),
    )

    assert determine_gama(150, gama_range) == "LUXURY"
    session.close()


def test_assign_gama_unitario_500_metal_returns_luxury_plus(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()
    gama_range = _build_gama_range(
        "METAL",
        medium=(0, 99.99),
        premium=(100, 199.99),
        luxury=(200, 399.99),
        luxury_plus=(400, 600),
    )

    assert determine_gama(500, gama_range) == "LUXURY_PLUS"
    session.close()


def test_find_gama_range_missing_category_returns_none_and_sin_clasificar(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()

    assert find_gama_range(session, "categoria_inexistente") is None
    assert determine_gama(123, None) == "SIN_CLASIFICAR"

    session.close()


def test_assign_gama_unitario_10_porcelana_returns_medium(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()
    gama_range = _build_gama_range(
        "PORCELANA",
        medium=(0, 19.99),
        premium=(20, 49.99),
        luxury=(50, 99.99),
        luxury_plus=(100, 199.99),
    )

    assert determine_gama(10, gama_range) == "MEDIUM"
    session.close()


def test_assign_gama_out_of_defined_ranges_returns_sin_clasificar(client_and_session):
    _, SessionLocal = client_and_session
    session = SessionLocal()
    gama_range = _build_gama_range(
        "METAL",
        medium=(0, 99.99),
        premium=(100, 199.99),
        luxury=(200, 399.99),
        luxury_plus=(400, 600),
    )

    assert determine_gama(700, gama_range) == "SIN_CLASIFICAR"
    session.close()


def test_endpoint_get_items_with_gamas_returns_gama_asignada_field(client_and_session):
    client, SessionLocal = client_and_session
    session = SessionLocal()

    session.add_all(
        [
            _build_gama_range(
                "PORCELANA",
                medium=(0, 19.99),
                premium=(20, 49.99),
                luxury=(50, 99.99),
                luxury_plus=(100, 199.99),
            ),
            ItemMaster(
                item_key="azulejo porcelanico rectificado",
                categoria="PORCELANA",
                unidad="m2",
                mediana_unitario=25.0,
                media_unitario=25.0,
                min_unitario=25.0,
                max_unitario=25.0,
                muestras_count=3,
            ),
        ]
    )
    session.commit()
    session.close()

    response = client.get("/api/items/with_gamas")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload["items"], list)
    assert payload["total_count"] >= 1
    assert "gama_asignada" in payload["items"][0]
    assert payload["items"][0]["gama_asignada"] == "PREMIUM"
