"""Integration tests for POST /api/import/budgets (TASK 5B + 5D)."""

from __future__ import annotations

import hashlib

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
    """Return a deterministic SHA256 hex string (64 chars) for testing."""
    return hashlib.sha256(seed.encode()).hexdigest()


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


# ---------------------------------------------------------------------------
# Suite 6: TASK 5D — Validaciones mejoradas y edge cases
# ---------------------------------------------------------------------------

class TestTask5DEdgeCases:
    def test_hash_no_hex_devuelve_422(self, client_and_session):
        """Hash con caracteres no hexadecimales rechazado en Pydantic."""
        client, _ = client_and_session
        resp = _post(client, {
            "file_hash": "not_a_valid_hash_not_a_valid_hash_not_a_valid_hash_not_a_valid_ha",
            "lineas": [{"numero": 1, "descripcion": "Algo", "cantidad": 1.0, "precio_unitario": 10.0}],
        })
        assert resp.status_code == 422

    def test_hash_63_chars_devuelve_422(self, client_and_session):
        """Hash hex de 63 caracteres (un carácter corto) → 422."""
        client, _ = client_and_session
        resp = _post(client, {
            "file_hash": "a" * 63,
            "lineas": [{"numero": 1, "descripcion": "Algo", "cantidad": 1.0, "precio_unitario": 10.0}],
        })
        assert resp.status_code == 422

    def test_hash_65_chars_devuelve_422(self, client_and_session):
        """Hash hex de 65 caracteres (uno de más) → 422."""
        client, _ = client_and_session
        resp = _post(client, {
            "file_hash": "a" * 65,
            "lineas": [{"numero": 1, "descripcion": "Algo", "cantidad": 1.0, "precio_unitario": 10.0}],
        })
        assert resp.status_code == 422

    def test_cantidad_negativa_linea_omitida(self, client_and_session):
        """Una línea con cantidad negativa se omite; la válida se procesa → partial."""
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("task5d_neg_qty_017"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida válida task5d", "cantidad": 10.0, "precio_unitario": 100.0},
                {"numero": 2, "descripcion": "Partida negativa task5d", "cantidad": -5.0, "precio_unitario": 100.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "partial"
        assert data["items_creados"] == 1

    def test_todas_invalidas_negativas_devuelve_error(self, client_and_session):
        """Todas las líneas con cantidad negativa → status error."""
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("task5d_all_neg_018"),
            "lineas": [
                {"numero": 1, "descripcion": "Solo negativas A", "cantidad": -1.0, "precio_unitario": 100.0},
                {"numero": 2, "descripcion": "Solo negativas B", "cantidad": -2.0, "precio_unitario": 50.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "error"
        assert data["items_creados"] == 0

    def test_partial_mezcla_validas_e_invalidas(self, client_and_session):
        """Mix: 2 válidas + 1 con desc vacía → partial con items_creados >= 2."""
        client, _ = client_and_session
        payload = {
            "file_hash": _make_hash("task5d_partial_mix_019"),
            "lineas": [
                {"numero": 1, "descripcion": "Partida mix A task5d", "cantidad": 10.0, "precio_unitario": 100.0},
                {"numero": 2, "descripcion": "", "cantidad": 5.0, "precio_unitario": 50.0},
                {"numero": 3, "descripcion": "Partida mix B task5d", "cantidad": 8.0, "precio_unitario": 75.0},
            ],
        }
        data = _post(client, payload).json()
        assert data["status"] == "partial"
        assert data["items_creados"] == 2


# ---------------------------------------------------------------------------
# Suite 7: TASK 6 — ImportService directo (sin HTTP)
# ---------------------------------------------------------------------------

@pytest.fixture
def direct_session():
    """Sesión SQLite aislada para tests del servicio sin FastAPI."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _linea(descripcion: str, cantidad: float = 10.0, precio: float = 100.0, numero: int = 1):
    from app.schemas.import_budgets import LineaPresupuesto
    return LineaPresupuesto(numero=numero, descripcion=descripcion, cantidad=cantidad, precio_unitario=precio)


class TestImportService:
    def test_service_importar_returns_response(self, direct_session):
        from app.services.import_service import ImportService
        service = ImportService(direct_session)
        result = service.importar(
            filename="test.xlsx",
            file_hash="a" * 64,
            building_type="residencial",
            lineas=[_linea("Solería porcelánica 60x60")],
        )
        assert result.status == "success"
        assert result.items_creados == 1
        assert result.muestras_actualizadas == 1

    def test_service_dedup_mismo_payload(self, direct_session):
        from app.services.import_service import ImportService
        service = ImportService(direct_session)
        result = service.importar(
            filename="test.xlsx",
            file_hash="b" * 64,
            building_type="residencial",
            lineas=[
                _linea("PINTURA PLÁSTICA BLANCA", numero=1),
                _linea("Pintura Plástica Blanca", numero=2),
            ],
        )
        assert result.items_creados == 1
        assert result.items_duplicados == 1

    def test_service_duplicate_hash_raises(self, direct_session):
        from app.services.import_service import DuplicateImportError, ImportService
        svc1 = ImportService(direct_session)
        svc1.importar(
            filename="presupuesto.xlsx",
            file_hash="c" * 64,
            building_type="residencial",
            lineas=[_linea("Hormigón HA-25")],
        )
        svc2 = ImportService(direct_session)
        with pytest.raises(DuplicateImportError) as exc_info:
            svc2.importar(
                filename="presupuesto.xlsx",
                file_hash="c" * 64,
                building_type="residencial",
                lineas=[_linea("Hormigón HA-25")],
            )
        assert exc_info.value.file_hash == "c" * 64

    def test_service_lineas_invalidas_status_error(self, direct_session):
        from app.services.import_service import ImportService
        service = ImportService(direct_session)
        result = service.importar(
            filename="vacio.xlsx",
            file_hash="d" * 64,
            building_type="residencial",
            lineas=[_linea("Algo", cantidad=-1.0)],
        )
        assert result.status == "error"
        assert result.items_creados == 0

    def test_service_partial_mix(self, direct_session):
        from app.services.import_service import ImportService
        service = ImportService(direct_session)
        result = service.importar(
            filename="mix.xlsx",
            file_hash="e" * 64,
            building_type="residencial",
            lineas=[
                _linea("Baldosa hidráulica", numero=1),
                _linea("Sin cantidad", cantidad=-5.0, numero=2),
            ],
        )
        assert result.status == "partial"
        assert result.items_creados == 1

    def test_service_muestras_count_acumulado(self, direct_session):
        from app.services.import_service import ImportService
        from src.db.schema import ItemMaster
        svc1 = ImportService(direct_session)
        svc1.importar(
            filename="a.xlsx", file_hash="f" * 64, building_type="residencial",
            lineas=[_linea("Aplacado pétreo mármol")],
        )
        svc2 = ImportService(direct_session)
        svc2.importar(
            filename="b.xlsx", file_hash="1" * 64, building_type="residencial",
            lineas=[_linea("Aplacado pétreo mármol")],
        )
        master = direct_session.query(ItemMaster).filter_by(
            item_key="aplacado petreo marmol"
        ).first()
        assert master.muestras_count == 2
