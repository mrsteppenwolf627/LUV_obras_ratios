"""Tests for FASE 2: GET /api/ratios/chapters + POST /api/analyze/comparativa."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, Budget, LineItem, Ratio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def api_client():
    """TestClient with an in-memory SQLite DB that has known ratio data."""
    from app import database as db_module
    from app import main as app_module
    from app.routers import visuales as vis_module

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

    # Seed: 1 budget + 2 chapters with ratios
    session = _Session()
    budget = Budget(
        filename="seed.xlsx",
        file_hash="s" * 64,
        source_format="excel",
        total_cost=180_000.0,
        surface_m2=300.0,
        building_type="residential",
    )
    session.add(budget)
    session.flush()

    for code, name, total in [
        ("ESTRUCTURA", "Estructura", 90_000.0),
        ("INSTALACIONES", "Instalaciones", 45_000.0),
    ]:
        session.add(
            LineItem(
                budget_id=budget.id,
                chapter_code=code,
                chapter_name=name,
                total_cost=total,
                validation_status="VALID",
            )
        )
    session.flush()

    # Add pre-computed Ratio rows directly
    for code, name, median, n in [
        ("ESTRUCTURA", "Estructura", 300.0, 3),
        ("INSTALACIONES", "Instalaciones", 150.0, 7),
        ("CIMENTACION", "Cimentación", 200.0, 12),
    ]:
        session.add(
            Ratio(
                chapter_code=code,
                chapter_name=name,
                building_type=None,
                median=median,
                min_value=median * 0.8,
                max_value=median * 1.2,
                sample_count=n,
            )
        )
    session.commit()
    session.close()

    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db
    vis_module._db.get_db = _fake_get_db  # patch the module-reference the router uses

    # Invalidate any stale cache from previous test runs
    from app.routers.visuales import invalidar_cache_chapters
    invalidar_cache_chapters()

    client = TestClient(app_module.app)
    yield client

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db
    vis_module._db.get_db = original_get_db


# ---------------------------------------------------------------------------
# GET /api/ratios/chapters
# ---------------------------------------------------------------------------


class TestGetRatiosChapters:
    def test_returns_200(self, api_client):
        resp = api_client.get("/api/ratios/chapters")
        assert resp.status_code == 200

    def test_returns_list(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        assert isinstance(data, list)

    def test_chapters_have_required_fields(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        assert len(data) > 0
        chapter = data[0]
        for field in ("capitulo", "mediana", "estado_confiabilidad", "cantidad_datos"):
            assert field in chapter, f"Missing field: {field}"

    def test_chapters_have_percentile_fields(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        assert len(data) > 0
        chapter = data[0]
        assert "percentil_25" in chapter
        assert "percentil_75" in chapter
        assert "desviacion_std" in chapter

    def test_confiabilidad_values_are_valid(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        valid_states = {"muy_solido", "solido", "debil", "muy_debil"}
        for ch in data:
            assert ch["estado_confiabilidad"] in valid_states

    def test_confiabilidad_muy_solido_for_high_count(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        # CIMENTACION has n=12 → muy_solido
        ciment = next((c for c in data if c["capitulo"] == "CIMENTACION"), None)
        assert ciment is not None
        assert ciment["estado_confiabilidad"] == "muy_solido"

    def test_confiabilidad_solido_for_medium_count(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        # INSTALACIONES has n=7 → solido
        inst = next((c for c in data if c["capitulo"] == "INSTALACIONES"), None)
        assert inst is not None
        assert inst["estado_confiabilidad"] == "solido"

    def test_confiabilidad_debil_for_low_count(self, api_client):
        data = api_client.get("/api/ratios/chapters").json()
        # ESTRUCTURA has n=3 → debil
        est = next((c for c in data if c["capitulo"] == "ESTRUCTURA"), None)
        assert est is not None
        assert est["estado_confiabilidad"] == "debil"

    def test_cache_returns_same_data(self, api_client):
        r1 = api_client.get("/api/ratios/chapters").json()
        r2 = api_client.get("/api/ratios/chapters").json()
        assert r1 == r2


# ---------------------------------------------------------------------------
# POST /api/analyze/comparativa
# ---------------------------------------------------------------------------


class TestAnalyzeComparativa:
    def _post(self, api_client, payload):
        return api_client.post("/api/analyze/comparativa", json=payload)

    def test_returns_200(self, api_client):
        resp = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 320.0}],
            "area_total": 200.0,
        })
        assert resp.status_code == 200

    def test_response_has_required_keys(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 320.0}],
            "area_total": 200.0,
        }).json()
        assert "capitulos" in data
        assert "capitulos_sin_ratio" in data
        assert "resumen" in data

    def test_resumen_area_total_matches_input(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 320.0}],
            "area_total": 250.0,
        }).json()
        assert data["resumen"]["area_total"] == 250.0

    def test_desviacion_pct_exact_value(self, api_client):
        # ESTRUCTURA ratio=300, user=320 → dev = (320-300)/300*100 = 6.67%
        data = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 320.0}],
            "area_total": 100.0,
        }).json()
        assert len(data["capitulos"]) == 1
        assert abs(data["capitulos"][0]["desviacion_pct"] - 6.67) < 0.1

    def test_impacto_monetario_exact_value(self, api_client):
        # dev=6.67%, ratio=300, area=100 → impacto = 6.67/100*300*100 = 2000€
        data = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 320.0}],
            "area_total": 100.0,
        }).json()
        assert abs(data["capitulos"][0]["impacto_monetario"] - 2000.0) < 1.0

    def test_unknown_chapter_goes_to_sin_ratio(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "CAPITULO_FICTICIO_XYZ", "valor_unitario": 100.0}],
            "area_total": 100.0,
        }).json()
        assert "CAPITULO_FICTICIO_XYZ" in data["capitulos_sin_ratio"]
        assert len(data["capitulos"]) == 0

    def test_case_insensitive_chapter_lookup(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "estructura", "valor_unitario": 300.0}],
            "area_total": 100.0,
        }).json()
        # Should find ESTRUCTURA
        assert len(data["capitulos"]) == 1
        assert data["capitulos"][0]["ratio_encontrado"] is True

    def test_confiabilidad_global_is_weakest(self, api_client):
        # ESTRUCTURA n=3 (debil), CIMENTACION n=12 (muy_solido) → global=debil
        data = self._post(api_client, {
            "items": [
                {"capitulo": "ESTRUCTURA", "valor_unitario": 300.0},
                {"capitulo": "CIMENTACION", "valor_unitario": 200.0},
            ],
            "area_total": 100.0,
        }).json()
        assert data["resumen"]["confiabilidad_global"] == "debil"

    def test_all_sin_ratio_gives_muy_debil(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "XXXNOEXISTE", "valor_unitario": 100.0}],
            "area_total": 100.0,
        }).json()
        assert data["resumen"]["confiabilidad_global"] == "muy_debil"

    def test_validation_error_area_total_zero(self, api_client):
        resp = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 300.0}],
            "area_total": 0.0,
        })
        assert resp.status_code == 422  # Pydantic gt=0 validation

    def test_validation_error_area_total_negative(self, api_client):
        resp = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 300.0}],
            "area_total": -100.0,
        })
        assert resp.status_code == 422

    def test_validation_error_empty_items(self, api_client):
        resp = self._post(api_client, {"items": [], "area_total": 100.0})
        assert resp.status_code == 422

    def test_validation_error_blank_chapter(self, api_client):
        resp = self._post(api_client, {
            "items": [{"capitulo": "   ", "valor_unitario": 300.0}],
            "area_total": 100.0,
        })
        assert resp.status_code == 422

    def test_validation_error_blank_unit(self, api_client):
        resp = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 300.0, "unidad": "   "}],
            "area_total": 100.0,
        })
        assert resp.status_code == 422

    def test_multiple_chapters_totals(self, api_client):
        data = self._post(api_client, {
            "items": [
                {"capitulo": "ESTRUCTURA", "valor_unitario": 300.0},
                {"capitulo": "INSTALACIONES", "valor_unitario": 150.0},
            ],
            "area_total": 100.0,
        }).json()
        # User matches ratios exactly → diferencia_monetaria ≈ 0
        assert abs(data["resumen"]["diferencia_monetaria"]) < 1.0
        assert len(data["capitulos"]) == 2

    def test_quantity_is_used_as_weight_in_chapter_average(self, api_client):
        data = self._post(api_client, {
            "items": [
                {"capitulo": "ESTRUCTURA", "valor_unitario": 300.0, "cantidad": 1},
                {"capitulo": "ESTRUCTURA", "valor_unitario": 450.0, "cantidad": 3},
            ],
            "area_total": 100.0,
        }).json()
        assert len(data["capitulos"]) == 1
        assert data["capitulos"][0]["valor_mio"] == 412.5
        assert data["capitulos"][0]["desviacion_pct"] == 37.5

    def test_building_type_is_trimmed_in_lookup(self, api_client):
        data = self._post(api_client, {
            "items": [{"capitulo": "ESTRUCTURA", "valor_unitario": 300.0}],
            "area_total": 100.0,
            "building_type": " residential ",
        }).json()
        assert len(data["capitulos"]) == 1
