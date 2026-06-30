"""Tests for POST /api/items/analisis (FASE C Task 3)."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.routers.items_analisis import normalizar_item_key
from src.db.schema import Base, Confianza, ItemMaster, ItemMasterRatio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_client():
    """TestClient with in-memory SQLite. Patches db_module.get_db globally."""
    from app import database as db_module
    from app import main as app_module
    from app.routers import items_analisis as items_module

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
    items_module._db.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client, _Session  # yield both so tests can inspect DB

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    items_module._db.get_db = original_get_db


@pytest.fixture
def client_and_session(api_client):
    """Unpack api_client fixture into (client, Session factory)."""
    return api_client


def _post(client, payload):
    return client.post("/api/items/analisis", json=payload)


# ---------------------------------------------------------------------------
# Suite 0: normalizar_item_key (pure function)
# ---------------------------------------------------------------------------

class TestNormalizarItemKey:
    def test_lowercase(self):
        assert normalizar_item_key("CARPINTERIA") == "carpinteria"

    def test_accent_removal(self):
        assert normalizar_item_key("Carpintería") == "carpinteria"

    def test_spaces_preserved(self):
        assert normalizar_item_key("doble acristalamiento") == "doble acristalamiento"

    def test_special_chars_removed(self):
        assert normalizar_item_key("Item (especial) / prueba") == "item especial prueba"

    def test_full_description(self):
        result = normalizar_item_key("Carpintería Aluminio Doble Acristalamiento")
        assert result == "carpinteria aluminio doble acristalamiento"

    def test_trailing_leading_spaces_removed(self):
        result = normalizar_item_key(" !item! ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_multiple_spaces_collapsed(self):
        result = normalizar_item_key("item   con   espacios")
        assert "  " not in result


# ---------------------------------------------------------------------------
# Suite 1: Basics
# ---------------------------------------------------------------------------

class TestAnalisisBasics:
    def test_returns_200(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "Carpintería aluminio doble acristalamiento", "precio_unitario": 250.0}]})
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Parquet flotante multicapa", "precio_unitario": 80.0}]}).json()
        assert "items" in data
        assert "resumenes_por_categoria" in data
        assert "resumen_general" in data
        assert data["ratios_updated"] is False
        assert data["mode"] == "read_only"

    def test_single_item_returns_one_resultado(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Pintura plástica blanca", "precio_unitario": 15.0}]}).json()
        assert len(data["items"]) == 1

    def test_multiple_items_returns_all(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "items": [
                {"descripcion": "Azulejo metro blanco", "precio_unitario": 12.0},
                {"descripcion": "Ventana aluminio lacado RPT", "precio_unitario": 400.0},
                {"descripcion": "Mármol Carrara encimera", "precio_unitario": 900.0},
                {"descripcion": "Tarima roble flotante", "precio_unitario": 75.0},
                {"descripcion": "Pintura interior económica", "precio_unitario": 8.0},
            ]
        }
        data = _post(client, payload).json()
        assert len(data["items"]) == 5

    def test_item_sin_ratio_historico(self, client_and_session):
        client, Session = client_and_session
        # Use a unique description not previously submitted
        desc = "Elemento nuevo sin historico abc999"
        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 100.0}]}).json()
        item = data["items"][0]
        assert item["ratio_encontrado"] is False
        assert item["ratio_historico"] is None
        assert item["desviacion_pct"] is None
        assert item["impacto_monetario"] is None

    def test_item_sin_ratio_confianza_muy_debil(self, client_and_session):
        client, _ = client_and_session
        desc = "Item nuevo sin historial xyz888"
        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 100.0}]}).json()
        assert data["items"][0]["confianza"] == Confianza.MUY_DEBIL


# ---------------------------------------------------------------------------
# Suite 2: Classification
# ---------------------------------------------------------------------------

class TestClasificacion:
    def test_keywords_carpinteria_premium(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Carpintería doble acristalamiento alta gama", "precio_unitario": 300.0}]}).json()
        assert data["items"][0]["categoria"] == "PREMIUM"

    def test_keywords_marmol_luxury_plus(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Encimera mármol Carrara natural", "precio_unitario": 1200.0}]}).json()
        assert data["items"][0]["categoria"] == "LUXURY_PLUS"

    def test_keywords_azulejo_medium(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Azulejo cocina blanco estándar", "precio_unitario": 18.0}]}).json()
        assert data["items"][0]["categoria"] == "MEDIUM"

    def test_keywords_madera_maciza_luxury(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Puerta madera maciza lacada", "precio_unitario": 650.0}]}).json()
        assert data["items"][0]["categoria"] == "LUXURY"

    def test_fallback_precio_bajo_medium(self, client_and_session):
        client, _ = client_and_session
        # Description has no keywords → falls back to price (80 < 150 → MEDIUM)
        data = _post(client, {"items": [{"descripcion": "Partida sin clasificar tipo basica", "precio_unitario": 80.0}]}).json()
        assert data["items"][0]["categoria"] == "MEDIUM"

    def test_fallback_precio_alto_luxury_plus(self, client_and_session):
        client, _ = client_and_session
        # No keywords → price 950 > 800 → LUXURY_PLUS
        data = _post(client, {"items": [{"descripcion": "Partida indeterminada tipo superior", "precio_unitario": 950.0}]}).json()
        assert data["items"][0]["categoria"] == "LUXURY_PLUS"


# ---------------------------------------------------------------------------
# Suite 3: Read-only behaviour
# ---------------------------------------------------------------------------

class TestReadOnlyMode:
    def test_endpoint_does_not_call_update_ratio_incremental(
        self, client_and_session, monkeypatch
    ):
        client, _ = client_and_session
        called = {"count": 0}

        def _boom(*_args, **_kwargs):
            called["count"] += 1
            raise AssertionError("update_ratio_incremental() no debe llamarse en T8")

        monkeypatch.setattr("app.crud.item_master_ratios.update_ratio_incremental", _boom)

        resp = _post(
            client,
            {"items": [{"descripcion": "Analisis solo lectura test001", "precio_unitario": 200.0}]},
        )
        assert resp.status_code == 200
        assert called["count"] == 0

    def test_item_master_ratio_no_cambia_tras_llamar_endpoint(self, client_and_session):
        client, Session = client_and_session
        desc = "Item readonly no change test002"
        key = normalizar_item_key(desc)

        session = Session()
        master = ItemMaster(item_key=key, categoria_asignada="PREMIUM")
        session.add(master)
        session.flush()
        session.add(
            ItemMasterRatio(
                item_master_id=master.id,
                categoria="PREMIUM",
                ratio_actual=200.0,
                mediana=200.0,
                muestras_count=3,
                confianza=str(Confianza.DEBIL),
                ultima_actualizacion=datetime.utcnow(),
            )
        )
        session.commit()
        master_id = master.id
        session.close()

        data = _post(
            client,
            {"items": [{"descripcion": desc, "precio_unitario": 240.0, "cantidad": 2.0}]},
        ).json()
        assert data["items"][0]["ratio_historico"] == pytest.approx(200.0)
        assert data["items"][0]["desviacion_pct"] == pytest.approx(20.0, abs=0.01)

        session = Session()
        ratio = session.query(ItemMasterRatio).filter_by(item_master_id=master_id).first()
        assert ratio.ratio_actual == pytest.approx(200.0)
        assert ratio.muestras_count == 3
        session.close()

    def test_unknown_item_remains_read_only_and_creates_no_ratio(self, client_and_session):
        client, Session = client_and_session
        desc = "Item nuevo solo lectura test003"
        key = normalizar_item_key(desc)

        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 300.0}]}).json()
        item = data["items"][0]
        assert item["ratio_encontrado"] is False
        assert item["ratio_historico"] is None

        session = Session()
        master = session.query(ItemMaster).filter_by(item_key=key).first()
        assert master is None
        session.close()


# ---------------------------------------------------------------------------
# Suite 4: Deviation calculations
# ---------------------------------------------------------------------------

class TestDesviaciones:
    def _seed_ratio(self, Session, desc: str, ratio_val: float, categoria: str) -> None:
        """Pre-seed an ItemMaster + ItemMasterRatio so next call has history."""
        key = normalizar_item_key(desc)
        session = Session()
        master = session.query(ItemMaster).filter_by(item_key=key).first()
        if master is None:
            master = ItemMaster(item_key=key, categoria_asignada=categoria)
            session.add(master)
            session.flush()
        existing = session.query(ItemMasterRatio).filter_by(
            item_master_id=master.id, categoria=categoria
        ).first()
        if existing is None:
            session.add(ItemMasterRatio(
                item_master_id=master.id,
                categoria=categoria,
                ratio_actual=ratio_val,
                mediana=ratio_val,
                muestras_count=3,
                confianza=str(Confianza.DEBIL),
                ultima_actualizacion=datetime.utcnow(),
            ))
        session.commit()
        session.close()

    def test_desviacion_positiva(self, client_and_session):
        client, Session = client_and_session
        desc = "Tarima roble flotante test_dev_pos"
        self._seed_ratio(Session, desc, 200.0, "PREMIUM")
        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 240.0}]}).json()
        item = data["items"][0]
        # (240-200)/200*100 = 20%
        assert item["desviacion_pct"] == pytest.approx(20.0, abs=0.01)
        assert item["ratio_encontrado"] is True

    def test_desviacion_negativa(self, client_and_session):
        client, Session = client_and_session
        desc = "Tarima roble flotante test_dev_neg"
        self._seed_ratio(Session, desc, 200.0, "PREMIUM")
        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 160.0}]}).json()
        item = data["items"][0]
        # (160-200)/200*100 = -20%
        assert item["desviacion_pct"] == pytest.approx(-20.0, abs=0.01)

    def test_desviacion_sin_ratio(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Item completamente nuevo sin hist zz7", "precio_unitario": 100.0}]}).json()
        assert data["items"][0]["desviacion_pct"] is None

    def test_impacto_usa_cantidad(self, client_and_session):
        client, Session = client_and_session
        desc = "Tarima roble flotante test_impacto"
        self._seed_ratio(Session, desc, 200.0, "PREMIUM")
        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 240.0, "cantidad": 5.0}]}).json()
        item = data["items"][0]
        # impacto = desviacion_pct * cantidad = 20 * 5 = 100
        assert item["impacto_monetario"] == pytest.approx(100.0, abs=0.01)


# ---------------------------------------------------------------------------
# Suite 5: Summaries
# ---------------------------------------------------------------------------

class TestResumenes:
    def test_resumen_general_keys(self, client_and_session):
        client, _ = client_and_session
        data = _post(client, {"items": [{"descripcion": "Azulejo cocina básica", "precio_unitario": 12.0}]}).json()
        rg = data["resumen_general"]
        for key in ("total_usuario", "total_ratio", "diferencia_pct", "items_con_ratio", "items_sin_ratio"):
            assert key in rg

    def test_resumen_general_items_sin_ratio(self, client_and_session):
        client, _ = client_and_session
        desc1 = "Item no en historico aaa111"
        desc2 = "Item no en historico bbb222"
        data = _post(client, {"items": [
            {"descripcion": desc1, "precio_unitario": 100.0},
            {"descripcion": desc2, "precio_unitario": 200.0},
        ]}).json()
        assert data["resumen_general"]["items_sin_ratio"] == 2
        assert data["resumen_general"]["items_con_ratio"] == 0

    def test_resumen_por_categoria_agrupado(self, client_and_session):
        client, _ = client_and_session
        # Two MEDIUM items, one LUXURY_PLUS
        payload = {
            "items": [
                {"descripcion": "Azulejo básico resumen test", "precio_unitario": 10.0},
                {"descripcion": "Pintura plástica resumen test", "precio_unitario": 12.0},
                {"descripcion": "Mármol travertino resumen test", "precio_unitario": 800.0},
            ]
        }
        data = _post(client, payload).json()
        cats = data["resumenes_por_categoria"]
        assert "MEDIUM" in cats
        assert "LUXURY_PLUS" in cats
        assert cats["MEDIUM"]["cantidad_items"] == 2
        assert cats["LUXURY_PLUS"]["cantidad_items"] == 1

    def test_resumen_por_categoria_precio_total(self, client_and_session):
        client, _ = client_and_session
        payload = {
            "items": [
                {"descripcion": "Azulejo basico total test ccc111", "precio_unitario": 15.0, "cantidad": 1.0},
                {"descripcion": "Pintura plastica total test ddd222", "precio_unitario": 20.0, "cantidad": 1.0},
            ]
        }
        data = _post(client, payload).json()
        cats = data["resumenes_por_categoria"]
        medium = cats.get("MEDIUM")
        if medium:
            assert medium["precio_total_usuario"] == pytest.approx(15.0 + 20.0, abs=0.01)

    def test_resumen_confianza_global_es_la_mas_debil(self, client_and_session):
        client, Session = client_and_session
        desc_premium = "Doble acristalamiento confianza test eee"
        desc_medium = "Pintura basica confianza test fff"
        # Seed PREMIUM with SOLIDO, MEDIUM with DEBIL
        session = Session()
        for desc, cat, conf, rat in [
            (desc_premium, "PREMIUM", str(Confianza.SOLIDO), 300.0),
            (desc_medium, "MEDIUM", str(Confianza.DEBIL), 15.0),
        ]:
            key = normalizar_item_key(desc)
            master = session.query(ItemMaster).filter_by(item_key=key).first()
            if master is None:
                master = ItemMaster(item_key=key, categoria_asignada=cat)
                session.add(master)
                session.flush()
            session.add(ItemMasterRatio(
                item_master_id=master.id, categoria=cat,
                ratio_actual=rat, mediana=rat, muestras_count=5,
                confianza=conf, ultima_actualizacion=datetime.utcnow(),
            ))
        session.commit()
        session.close()

        data = _post(client, {"items": [
            {"descripcion": desc_premium, "precio_unitario": 310.0},
            {"descripcion": desc_medium, "precio_unitario": 14.0},
        ]}).json()

        # PREMIUM should show SOLIDO, MEDIUM shows DEBIL
        assert data["resumenes_por_categoria"]["PREMIUM"]["confianza_global"] == str(Confianza.SOLIDO)
        assert data["resumenes_por_categoria"]["MEDIUM"]["confianza_global"] == str(Confianza.DEBIL)


# ---------------------------------------------------------------------------
# Suite 6: E2E
# ---------------------------------------------------------------------------

class TestE2E:
    def test_e2e_sin_historico_todas_read_only(self, client_and_session):
        client, Session = client_and_session
        items = [
            {"descripcion": "E2E primer item aluminio lacado ggg", "precio_unitario": 350.0},
            {"descripcion": "E2E segundo item azulejo basico hhh", "precio_unitario": 10.0},
        ]
        data = _post(client, {"items": items}).json()
        assert all(not i["ratio_encontrado"] for i in data["items"])
        assert data["resumen_general"]["items_sin_ratio"] == 2
        assert data["ratios_updated"] is False

        session = Session()
        for item in items:
            key = normalizar_item_key(item["descripcion"])
            master = session.query(ItemMaster).filter_by(item_key=key).first()
            assert master is None
        session.close()

    def test_e2e_con_historico_calcula_desviacion(self, client_and_session):
        client, Session = client_and_session
        desc = "E2E item con historico previo iii999"
        session = Session()
        key = normalizar_item_key(desc)
        master = ItemMaster(item_key=key, categoria_asignada="PREMIUM")
        session.add(master)
        session.flush()
        session.add(
            ItemMasterRatio(
                item_master_id=master.id,
                categoria="PREMIUM",
                ratio_actual=300.0,
                mediana=300.0,
                muestras_count=3,
                confianza=str(Confianza.DEBIL),
                ultima_actualizacion=datetime.utcnow(),
            )
        )
        session.commit()
        session.close()

        data = _post(client, {"items": [{"descripcion": desc, "precio_unitario": 360.0}]}).json()
        item = data["items"][0]
        assert item["ratio_encontrado"] is True
        assert item["ratio_historico"] == pytest.approx(300.0)
        assert item["desviacion_pct"] == pytest.approx(20.0, abs=0.01)

    def test_e2e_ratio_no_se_actualiza_en_bd(self, client_and_session):
        client, Session = client_and_session
        desc = "E2E ratio actualizado jjj000"
        key = normalizar_item_key(desc)
        session = Session()
        master = ItemMaster(item_key=key, categoria_asignada="PREMIUM")
        session.add(master)
        session.flush()
        session.add(
            ItemMasterRatio(
                item_master_id=master.id,
                categoria="PREMIUM",
                ratio_actual=200.0,
                mediana=200.0,
                muestras_count=1,
                confianza=str(Confianza.MUY_DEBIL),
                ultima_actualizacion=datetime.utcnow(),
            )
        )
        session.commit()
        master_id = master.id
        session.close()

        _post(client, {"items": [{"descripcion": desc, "precio_unitario": 400.0}]})

        session = Session()
        ratio = session.query(ItemMasterRatio).filter_by(item_master_id=master_id).first()
        assert ratio.muestras_count == 1
        assert ratio.ratio_actual == pytest.approx(200.0)
        session.close()

    def test_e2e_con_area_total_aceptada(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {
            "items": [{"descripcion": "Parquet flotante e2e area", "precio_unitario": 70.0}],
            "area_total": 120.0,
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Suite 7: Input validation
# ---------------------------------------------------------------------------

class TestValidacion:
    def test_error_items_vacio(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": []})
        assert resp.status_code == 422

    def test_error_precio_negativo(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "Item valido", "precio_unitario": -100.0}]})
        assert resp.status_code == 422

    def test_error_precio_cero(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "Item valido", "precio_unitario": 0.0}]})
        assert resp.status_code == 422

    def test_error_descripcion_vacia(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "   ", "precio_unitario": 100.0}]})
        assert resp.status_code == 422

    def test_error_descripcion_muy_corta(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "ab", "precio_unitario": 100.0}]})
        assert resp.status_code == 422

    def test_error_area_total_negativa(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {
            "items": [{"descripcion": "Item valido prueba", "precio_unitario": 100.0}],
            "area_total": -50.0,
        })
        assert resp.status_code == 422

    def test_error_cantidad_cero(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "Item valido prueba", "precio_unitario": 100.0, "cantidad": 0}]})
        assert resp.status_code == 422

    def test_descripcion_con_espacios_es_valida(self, client_and_session):
        client, _ = client_and_session
        resp = _post(client, {"items": [{"descripcion": "Azulejo ceramico blanco", "precio_unitario": 15.0}]})
        assert resp.status_code == 200
