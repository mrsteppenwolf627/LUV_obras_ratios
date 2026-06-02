"""Integration tests for POST /api/import/budgets (TASK 5B)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, BudgetImport, ItemMaster


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_client():
    """TestClient with in-memory SQLite. Patches get_db globally."""
    from app import database as db_module
    from app import main as app_module
    from app.routers import import_budgets as import_module

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

    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db
    import_module._db.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client, _Session

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    import_module._db.get_db = original_get_db


@pytest.fixture
def client_and_session(api_client):
    return api_client


def _post(client, payload):
    return client.post("/api/import/budgets", json=payload)


def _make_hash(seed: str) -> str:
    """Return a deterministic 64-char hash-like string for testing."""
    base = seed.replace(" ", "_")
    return (base * 64)[:64]


# ---------------------------------------------------------------------------
# Suite 1: Importación válida
# ---------------------------------------------------------------------------

class TestImportValid:
    def test_import_valid_budget_returns_200(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "filename": "test_presupuesto.xlsx",
            "file_hash": _make_hash("valid_budget_001"),
            "building_type": "residencial",
            "lineas": [
                {
                    "numero": 1,
                    "capitulo": "01",
                    "descripcion": "Carpintería Aluminio",
                    "cantidad": 10.0,
                    "unidad": "m2",
                    "precio_unitario": 245.50,
                }
            ],
        }
        response = _post(client, payload)
        assert response.status_code == 200

    def test_import_valid_budget_status_success(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("valid_budget_002"),
            "lineas": [
                {
                    "numero": 1,
                    "descripcion": "Pintura plástica blanca",
                    "cantidad": 50.0,
                    "precio_unitario": 12.0,
                }
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "success"

    def test_import_valid_budget_items_creados(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("valid_budget_003"),
            "lineas": [
                {"numero": 1, "descripcion": "Azulejo blanco cocina", "cantidad": 20.0, "precio_unitario": 18.0},
                {"numero": 2, "descripcion": "Parquet flotante roble", "cantidad": 30.0, "precio_unitario": 65.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["items_creados"] == 2
        assert data["items_duplicados"] == 0
        assert data["muestras_actualizadas"] == 2

    def test_import_persists_item_master(self, client_and_session):
        client, Session = client_and_session
        file_hash = _make_hash("persist_test_004")
        payload = {
            "file_hash": file_hash,
            "lineas": [
                {"numero": 1, "descripcion": "Ventana aluminio lacado RPT", "cantidad": 5.0, "precio_unitario": 380.0}
            ],
        }
        _post(client, payload)

        session = Session()
        master = session.query(ItemMaster).filter_by(item_key="ventana aluminio lacado rpt").first()
        assert master is not None
        assert master.muestras_count == 1
        session.close()


# ---------------------------------------------------------------------------
# Suite 2: Deduplicación
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_mismo_item_key_en_mismo_payload_deduplica(self, client_and_session):
        client, _ = client_and_session
        # Usa clave única para este test (scope=module comparte la BD)
        payload = {
            "file_hash": _make_hash("dedup_same_batch_005"),
            "lineas": [
                {"numero": 1, "descripcion": "REVESTIMIENTO MÁRMOL ÚNICO XYZ", "cantidad": 10.0, "precio_unitario": 245.0},
                {"numero": 2, "descripcion": "Revestimiento Mármol Único XYZ", "cantidad": 5.0, "precio_unitario": 250.0},
                {"numero": 3, "descripcion": "revestimiento marmol unico xyz", "cantidad": 8.0, "precio_unitario": 248.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["items_creados"] == 1
        assert data["items_duplicados"] == 2

    def test_reimportar_item_existente_es_duplicado(self, client_and_session):
        client, Session = client_and_session
        # Primera importación crea el ItemMaster
        _post(client, {
            "file_hash": _make_hash("existing_item_first_006"),
            "lineas": [{"numero": 1, "descripcion": "Solado cerámico 30x30", "cantidad": 40.0, "precio_unitario": 22.0}],
        })
        # Segunda importación con el mismo item → duplicado
        data = _post(client, {
            "file_hash": _make_hash("existing_item_second_007"),
            "lineas": [{"numero": 1, "descripcion": "Solado cerámico 30x30", "cantidad": 20.0, "precio_unitario": 24.0}],
        }).json()
        assert data["items_duplicados"] == 1
        assert data["items_creados"] == 0

    def test_muestras_count_se_incrementa_por_linea(self, client_and_session):
        client, Session = client_and_session
        desc = "Mármol Carrara encimera test"
        item_key = "marmol carrara encimera test"

        _post(client, {
            "file_hash": _make_hash("muestras_count_008a"),
            "lineas": [{"numero": 1, "descripcion": desc, "cantidad": 2.0, "precio_unitario": 900.0}],
        })
        _post(client, {
            "file_hash": _make_hash("muestras_count_008b"),
            "lineas": [{"numero": 1, "descripcion": desc, "cantidad": 3.0, "precio_unitario": 850.0}],
        })

        session = Session()
        master = session.query(ItemMaster).filter_by(item_key=item_key).first()
        assert master.muestras_count == 2
        session.close()


# ---------------------------------------------------------------------------
# Suite 3: Re-importación → 409
# ---------------------------------------------------------------------------

class TestDuplicateHash:
    def test_reimport_same_hash_returns_409(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("duplicate_hash_009"),
            "lineas": [{"numero": 1, "descripcion": "Hormigón HA-25 losa", "cantidad": 100.0, "precio_unitario": 85.0}],
        }
        resp1 = _post(client, payload)
        assert resp1.status_code == 200

        resp2 = _post(client, payload)
        assert resp2.status_code == 409
        assert "Ya importado" in resp2.json()["detail"]

    def test_409_contiene_fragmento_del_hash(self, client_and_session):
        client, _ = client_and_session
        file_hash = _make_hash("hash_fragment_010")
        _post(client, {
            "file_hash": file_hash,
            "lineas": [{"numero": 1, "descripcion": "Estructura metálica pilares", "cantidad": 1.0, "precio_unitario": 200.0}],
        })
        resp = _post(client, {
            "file_hash": file_hash,
            "lineas": [{"numero": 1, "descripcion": "Estructura metálica pilares", "cantidad": 1.0, "precio_unitario": 200.0}],
        })
        assert file_hash[:8] in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Suite 4: Líneas inválidas (skip + partial)
# ---------------------------------------------------------------------------

class TestInvalidLineas:
    def test_linea_sin_cantidad_es_omitida(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("skip_no_cantidad_011"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida válida uno", "cantidad": 10.0, "precio_unitario": 100.0},
                {"numero": 2, "descripcion": "Partida sin cantidad", "precio_unitario": 100.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "partial"
        assert data["items_creados"] == 1

    def test_linea_con_cantidad_cero_es_omitida(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("skip_zero_cantidad_012"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida válida dos", "cantidad": 5.0, "precio_unitario": 50.0},
                {"numero": 2, "descripcion": "Partida cantidad cero", "cantidad": 0.0, "precio_unitario": 50.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "partial"
        assert data["items_creados"] == 1

    def test_linea_con_precio_cero_es_omitida(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("skip_zero_precio_013"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida válida tres", "cantidad": 5.0, "precio_unitario": 75.0},
                {"numero": 2, "descripcion": "Partida precio cero", "cantidad": 5.0, "precio_unitario": 0.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "partial"
        assert data["items_creados"] == 1

    def test_todas_las_lineas_invalidas_devuelve_error(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("all_invalid_014"),
            "lineas": [
                {"numero": 1, "descripcion": "Sin cantidad", "precio_unitario": 100.0},
                {"numero": 2, "descripcion": "Precio cero", "cantidad": 5.0, "precio_unitario": 0.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "error"
        assert data["items_creados"] == 0

    def test_detalles_incluye_razon_de_skip(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("detalles_skip_015"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida ok", "cantidad": 3.0, "precio_unitario": 30.0},
                {"numero": 2, "descripcion": "Sin cantidad aqui", "precio_unitario": 30.0},
            ],
        }
        data = _post(client, payload).json()
        assert any("omitida" in d.lower() for d in data["detalles"])


# ---------------------------------------------------------------------------
# Suite 5: Validación de request
# ---------------------------------------------------------------------------

class TestRequestValidation:
    def test_lineas_vacio_devuelve_422(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"file_hash": _make_hash("empty_lineas_016"), "lineas": []})
        assert resp.status_code == 422

    def test_file_hash_muy_corto_devuelve_422(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {
            "file_hash": "abc",
            "lineas": [{"numero": 1, "descripcion": "Algo", "cantidad": 1.0, "precio_unitario": 10.0}],
        })
        assert resp.status_code == 422
