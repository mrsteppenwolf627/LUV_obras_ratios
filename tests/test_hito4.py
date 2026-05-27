"""Tests for HITO 4: item extractor, classifier, ratio calculator, DB tables, API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_presto_budget(spaces: list[tuple[str, float]]) -> dict:
    """Minimal parse_presto() output."""
    from src.core.presto_reader import _resolve_zone
    return {
        "filename": "test.Presto",
        "source_format": "presto",
        "budget_code": "TST",
        "total_coste": sum(c for _, c in spaces),
        "total_m2": 0.0,
        "has_space_breakdown": True,
        "errors": [],
        "warnings": [],
        "espacios": [
            {
                "nombre": name,
                "zona": _resolve_zone(name),
                "planta": "TOTAL",
                "coste": cost,
                "m2": 0.0,
                "partidas": [
                    {
                        "codigo": f"{name[:6].replace(' ', '_')}.TOT",
                        "descripcion": f"Total {name}",
                        "cantidad": 1.0,
                        "unidad": "",
                        "unitario": cost,
                        "coste": cost,
                        "m2": 0.0,
                    }
                ],
            }
            for name, cost in spaces
        ],
    }


def _make_chapters_budget(chapters: list[tuple[str, str, float]]) -> dict:
    """Minimal read_bc3() / read_excel() output with chapters."""
    return {
        "filename": "test.bc3",
        "source_format": "bc3",
        "total_cost": sum(c for _, _, c in chapters),
        "errors": [],
        "warnings": [],
        "chapters": [
            {
                "chapter_code": code,
                "chapter_name": name,
                "total_cost": cost,
                "quantity": None,
                "unit": "",
                "unit_cost": None,
            }
            for code, name, cost in chapters
        ],
    }


@pytest.fixture()
def db_session():
    """In-memory SQLite session with all tables created."""
    from src.db.schema import Base
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ===========================================================================
# 1. ITEM EXTRACTOR
# ===========================================================================

class TestItemExtractor:
    def test_returns_list(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 5000.0)])
        result = extract_items_from_budget(budget)
        assert isinstance(result, list)

    def test_presto_one_item_per_partida(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 5000.0), ("COCINA", 3000.0)])
        result = extract_items_from_budget(budget)
        assert len(result) == 2

    def test_presto_item_has_required_keys(self):
        from src.core.item_extractor import extract_items_from_budget
        result = extract_items_from_budget(_make_presto_budget([("SALA", 1000.0)]))
        for key in ("codigo", "descripcion", "categoria_original", "cantidad",
                    "unidad", "precio_unitario", "precio_total",
                    "presupuesto_id", "validation_status", "dubious_reasons"):
            assert key in result[0], f"Missing key: {key}"

    def test_presto_categoria_original_is_space_name(self):
        from src.core.item_extractor import extract_items_from_budget
        result = extract_items_from_budget(_make_presto_budget([("SALA", 1000.0)]))
        assert result[0]["categoria_original"] == "SALA"

    def test_presto_precio_total_correct(self):
        from src.core.item_extractor import extract_items_from_budget
        result = extract_items_from_budget(_make_presto_budget([("SALA", 7500.0)]))
        assert abs(result[0]["precio_total"] - 7500.0) < 0.01

    def test_presto_budget_id_propagated(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 1000.0)])
        result = extract_items_from_budget(budget, budget_id=42)
        assert result[0]["presupuesto_id"] == 42

    def test_chapters_budget_extracts_items(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_chapters_budget([("C01", "Estructura", 50000.0)])
        result = extract_items_from_budget(budget)
        assert len(result) == 1

    def test_chapters_item_keys(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_chapters_budget([("C01", "Estructura", 50000.0)])
        item = extract_items_from_budget(budget)[0]
        assert item["codigo"] == "C01"
        assert item["descripcion"] == "Estructura"
        assert abs(item["precio_total"] - 50000.0) < 0.01

    def test_empty_chapters_returns_empty(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {"source_format": "bc3", "chapters": [], "errors": [], "warnings": []}
        assert extract_items_from_budget(budget) == []

    def test_dubious_when_zero_cost(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 0.0)])
        result = extract_items_from_budget(budget)
        assert result[0]["validation_status"] == "DUBIOUS"

    def test_valid_when_nonzero_cost(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 5000.0)])
        result = extract_items_from_budget(budget)
        assert result[0]["validation_status"] == "VALID"

    def test_precio_unitario_derived_from_total_and_cantidad(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {
            "source_format": "bc3",
            "chapters": [
                {
                    "chapter_code": "C01",
                    "chapter_name": "Pintura",
                    "total_cost": 1000.0,
                    "quantity": 10.0,
                    "unit": "m²",
                    "unit_cost": None,
                }
            ],
            "errors": [],
            "warnings": [],
        }
        result = extract_items_from_budget(budget)
        assert result[0]["precio_unitario"] == pytest.approx(100.0, abs=0.01)

    def test_unknown_format_tries_chapters_key(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {
            "chapters": [{"chapter_code": "X1", "chapter_name": "Test", "total_cost": 100.0}],
            "errors": [],
        }
        result = extract_items_from_budget(budget)
        assert len(result) == 1

    def test_unknown_format_tries_espacios_key(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = _make_presto_budget([("SALA", 1000.0)])
        del budget["source_format"]
        result = extract_items_from_budget(budget)
        assert len(result) == 1

    def test_make_item_key_normalizes(self):
        from src.core.item_extractor import make_item_key
        k1 = make_item_key("Hormigón HA-30", "m³")
        k2 = make_item_key("hormigón ha-30", "M³")
        assert k1 == k2

    def test_make_item_key_different_units_differ(self):
        from src.core.item_extractor import make_item_key
        k1 = make_item_key("Acero", "kg")
        k2 = make_item_key("Acero", "t")
        assert k1 != k2


# ===========================================================================
# 2. ITEM CLASSIFIER
# ===========================================================================

class TestItemClassifier:
    def _item(self, desc: str, unidad: str = "") -> dict:
        return {"descripcion": desc, "unidad": unidad}

    def test_returns_dict(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Hormigón HA-30"))
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Hormigón HA-30"))
        for k in ("categoria", "subcategoria", "keywords_detectados", "confianza", "reglas_aplicadas"):
            assert k in result

    def test_hormigon_is_estructura(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Hormigón HA-30 en cimentación"))["categoria"] == "ESTRUCTURA"

    def test_acero_is_estructura(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Acero B-500S"))["categoria"] == "ESTRUCTURA"

    def test_pintura_is_acabados(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Pintura plástica"))["categoria"] == "ACABADOS"

    def test_electricidad_is_instalaciones(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Cable eléctrico 2.5mm"))["categoria"] == "INSTALACIONES"

    def test_fontaneria_is_instalaciones(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Tubería de fontanería PVC"))["categoria"] == "INSTALACIONES"

    def test_demolicion_detected(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Derribo de tabique"))["categoria"] == "DEMOLICIÓN"

    def test_mueble_is_mobiliario(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Mueble de cocina"))["categoria"] == "MOBILIARIO"

    def test_unknown_item_returns_otros(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Partida sin descripcion XYZ123"))
        assert result["categoria"] == "OTROS"
        assert result["confianza"] == 0.0

    def test_confianza_between_0_and_1(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Hormigón HA-30", "m³"))
        assert 0.0 <= result["confianza"] <= 1.0

    def test_keywords_detected_nonempty_for_known_item(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Encofrado de madera"))
        assert len(result["keywords_detectados"]) > 0

    def test_unit_boosts_confidence(self):
        from src.ratios.item_classifier import classify_item
        r_with = classify_item(self._item("Hormigón HA-30", "m³"))
        r_without = classify_item(self._item("Hormigón HA-30", ""))
        assert r_with["confianza"] >= r_without["confianza"]

    def test_subcategoria_hormigonado(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Hormigón HA-25 en zapata"))
        assert result["subcategoria"] == "Hormigonado"

    def test_subcategoria_pintura(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Pintura plástica dos manos"))
        assert result["subcategoria"] == "Pintura"

    def test_reglas_aplicadas_nonempty(self):
        from src.ratios.item_classifier import classify_item
        result = classify_item(self._item("Acero corrugado B-500S"))
        assert len(result["reglas_aplicadas"]) > 0

    def test_case_insensitive(self):
        from src.ratios.item_classifier import classify_item
        r1 = classify_item(self._item("HORMIGÓN HA-30"))
        r2 = classify_item(self._item("hormigón ha-30"))
        assert r1["categoria"] == r2["categoria"]

    def test_excavacion_is_demolicion(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Excavación en zanja"))["categoria"] == "DEMOLICIÓN"

    def test_parquet_is_acabados(self):
        from src.ratios.item_classifier import classify_item
        assert classify_item(self._item("Tarima flotante de parquet"))["categoria"] == "ACABADOS"


# ===========================================================================
# 3. ITEM RATIO CALCULATOR — compute_stats
# ===========================================================================

class TestComputeStats:
    def test_empty_returns_empty_dict(self):
        from src.ratios.item_ratio_calculator import compute_stats
        assert compute_stats([]) == {}

    def test_single_price(self):
        from src.ratios.item_ratio_calculator import compute_stats
        result = compute_stats([100.0])
        assert result["mediana"] == pytest.approx(100.0)
        assert result["muestras_count"] == 1
        assert result["desv_std"] == 0.0

    def test_multiple_prices_mediana(self):
        from src.ratios.item_ratio_calculator import compute_stats
        result = compute_stats([100.0, 200.0, 150.0])
        assert result["mediana"] == pytest.approx(150.0)

    def test_min_max(self):
        from src.ratios.item_ratio_calculator import compute_stats
        result = compute_stats([50.0, 200.0, 125.0])
        assert result["min"] == pytest.approx(50.0)
        assert result["max"] == pytest.approx(200.0)

    def test_filters_zero_prices(self):
        from src.ratios.item_ratio_calculator import compute_stats
        result = compute_stats([0.0, 100.0, 200.0])
        assert result["muestras_count"] == 2

    def test_all_zero_returns_empty(self):
        from src.ratios.item_ratio_calculator import compute_stats
        assert compute_stats([0.0, 0.0]) == {}


# ===========================================================================
# 4. CLASSIFY_NEW_ITEM_PRICE
# ===========================================================================

class TestClassifyNewItemPrice:
    def _hist(self, prices: list[float]) -> dict:
        from src.ratios.item_ratio_calculator import compute_stats
        return compute_stats(prices)

    def test_no_history_returns_primera_muestra(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        result = classify_new_item_price({"precio_unitario": 100.0}, None)
        assert result["clasificacion"] == "PRIMERA_MUESTRA"

    def test_empty_history_returns_primera_muestra(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        result = classify_new_item_price({"precio_unitario": 100.0}, {})
        assert result["clasificacion"] == "PRIMERA_MUESTRA"

    def test_normal_price_within_15pct(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 110.0}, hist)
        assert result["clasificacion"] == "NORMAL"

    def test_caro_above_15pct(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 120.0}, hist)
        assert result["clasificacion"] == "CARO"

    def test_barato_below_15pct(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 80.0}, hist)
        assert result["clasificacion"] == "BARATO"

    def test_anomaly_above_30pct(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 135.0}, hist)
        assert result["clasificacion"] == "ANOMALÍA"

    def test_anomaly_below_30pct(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 65.0}, hist)
        assert result["clasificacion"] == "ANOMALÍA"

    def test_desviacion_porcentaje_calculated(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 120.0}, hist)
        assert result["desviacion_porcentaje"] == pytest.approx(20.0, abs=0.1)

    def test_no_precio_returns_sin_precio(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        result = classify_new_item_price({"precio_unitario": None}, self._hist([100.0]))
        assert result["clasificacion"] == "SIN_PRECIO"

    def test_confianza_alta_with_many_samples(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0] * 6)
        result = classify_new_item_price({"precio_unitario": 110.0}, hist)
        assert result["confianza"] == "ALTA"

    def test_confianza_baja_with_one_sample(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0])
        result = classify_new_item_price({"precio_unitario": 110.0}, hist)
        assert result["confianza"] == "BAJA"

    def test_has_accion_field(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([100.0, 100.0, 100.0])
        result = classify_new_item_price({"precio_unitario": 120.0}, hist)
        assert "accion" in result
        assert isinstance(result["accion"], str)


# ===========================================================================
# 5. DB — ItemMaster / ItemInstance
# ===========================================================================

class TestItemMasterDB:
    def test_create_item_master(self, db_session):
        from src.db.schema import ItemMaster
        m = ItemMaster(item_key="hormigon ha30|m3", categoria="ESTRUCTURA", muestras_count=0)
        db_session.add(m)
        db_session.commit()
        assert m.id is not None

    def test_item_key_unique_constraint(self, db_session):
        from sqlalchemy.exc import IntegrityError
        from src.db.schema import ItemMaster
        db_session.add(ItemMaster(item_key="dup_key|ud", categoria="OTROS"))
        db_session.commit()
        db_session.add(ItemMaster(item_key="dup_key|ud", categoria="OTROS"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_item_instance_linked_to_budget(self, db_session):
        from datetime import datetime, timezone
        from src.db.schema import Budget, ItemInstance, ItemMaster
        budget = Budget(
            filename="test.Presto",
            file_hash="abc123",
            source_format="presto",
            total_cost=1000.0,
        )
        db_session.add(budget)
        db_session.flush()

        master = ItemMaster(item_key="sala total|", categoria="NOBLE", muestras_count=0)
        db_session.add(master)
        db_session.flush()

        instance = ItemInstance(
            budget_id=budget.id,
            item_master_id=master.id,
            descripcion="Total SALA",
            precio_unitario=1000.0,
            precio_total=1000.0,
            validation_status="VALID",
        )
        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert instance.budget_id == budget.id
        assert instance.item_master_id == master.id

    def test_recalculate_stats_updates_master(self, db_session):
        from datetime import datetime, timezone
        from src.db.schema import Budget, ItemInstance, ItemMaster
        from src.ratios.item_ratio_calculator import recalculate_item_master_stats

        budget = Budget(filename="b.Presto", file_hash="xyz999", source_format="presto", total_cost=5000.0)
        db_session.add(budget)
        db_session.flush()

        master = ItemMaster(item_key="pintura|m2", categoria="ACABADOS", muestras_count=0)
        db_session.add(master)
        db_session.flush()

        for price in [100.0, 120.0, 110.0]:
            db_session.add(ItemInstance(
                budget_id=budget.id,
                item_master_id=master.id,
                descripcion="Pintura",
                precio_unitario=price,
                precio_total=price,
                validation_status="VALID",
            ))
        db_session.flush()

        updated = recalculate_item_master_stats(db_session, master.id)
        assert updated is True
        assert master.muestras_count == 3
        assert master.mediana_unitario == pytest.approx(110.0, abs=0.01)


# ===========================================================================
# 6. API ENDPOINTS (FastAPI TestClient)
# ===========================================================================

@pytest.fixture(scope="module")
def api_client():
    """TestClient backed by a shared in-memory SQLite DB (StaticPool)."""
    from sqlalchemy.pool import StaticPool
    from src.db.schema import Base
    from app import main as app_module
    from app import database as db_module

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    _Session = sessionmaker(bind=engine)

    original_get_db = db_module.get_db

    def _fake_get_db():
        return _Session()

    db_module.get_db = _fake_get_db
    app_module.get_db = _fake_get_db

    client = TestClient(app_module.app)
    yield client

    db_module.get_db = original_get_db
    app_module.get_db = original_get_db


class TestItemsAPI:
    def test_search_returns_200(self, api_client):
        resp = api_client.get("/api/items/search")
        assert resp.status_code == 200

    def test_search_response_has_items_key(self, api_client):
        resp = api_client.get("/api/items/search")
        data = resp.json()
        assert "items" in data

    def test_search_with_query_param(self, api_client):
        resp = api_client.get("/api/items/search?q=hormigon")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_search_with_categoria_param(self, api_client):
        resp = api_client.get("/api/items/search?categoria=ESTRUCTURA")
        assert resp.status_code == 200

    def test_by_category_returns_200(self, api_client):
        resp = api_client.get("/api/items/by-category?categoria=ESTRUCTURA")
        assert resp.status_code == 200

    def test_by_category_response_has_items(self, api_client):
        resp = api_client.get("/api/items/by-category?categoria=ESTRUCTURA")
        data = resp.json()
        assert "items" in data
        assert "categoria" in data

    def test_by_category_normalizes_to_uppercase(self, api_client):
        resp = api_client.get("/api/items/by-category?categoria=estructura")
        assert resp.status_code == 200
        assert resp.json()["categoria"] == "ESTRUCTURA"

    def test_item_history_404_when_not_found(self, api_client):
        resp = api_client.get("/api/items/nonexistent-key/history")
        assert resp.status_code == 404

    def test_search_count_field_present(self, api_client):
        resp = api_client.get("/api/items/search")
        assert "count" in resp.json()


# ===========================================================================
# 7. MULTI-UNIT TESTS (refactoring)
# ===========================================================================

class TestMultiUnit:
    """Ratios must work with ANY unit — not just m²."""

    # --- make_item_key ---

    def test_same_desc_different_units_produce_different_keys(self):
        from src.core.item_extractor import make_item_key
        k_m3 = make_item_key("Hormigón HA-30", "m³")
        k_kg = make_item_key("Hormigón HA-30", "kg")
        assert k_m3 != k_kg

    def test_same_desc_same_unit_produce_same_key(self):
        from src.core.item_extractor import make_item_key
        k1 = make_item_key("Pintura plástica", "l")
        k2 = make_item_key("Pintura plástica", "l")
        assert k1 == k2

    # --- classify_new_item_price — unit propagation ---

    def _hist(self, prices, unidad="m³"):
        from src.ratios.item_ratio_calculator import compute_stats
        stats = compute_stats(prices)
        stats["unidad"] = unidad
        return stats

    def test_result_includes_unidad(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([950.0, 950.0, 950.0], "t")
        result = classify_new_item_price({"precio_unitario": 950.0, "unidad": "t"}, hist)
        assert "unidad" in result
        assert result["unidad"] == "t"

    def test_unidad_diferente_when_units_mismatch(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([185.0, 185.0, 185.0], "m³")
        # New item is in kg — should refuse comparison
        result = classify_new_item_price({"precio_unitario": 0.5, "unidad": "kg"}, hist)
        assert result["clasificacion"] == "UNIDAD_DIFERENTE"

    def test_normal_when_units_match(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        hist = self._hist([185.0, 185.0, 185.0], "m³")
        result = classify_new_item_price({"precio_unitario": 190.0, "unidad": "m³"}, hist)
        assert result["clasificacion"] == "NORMAL"

    def test_caro_when_units_match_and_price_high(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        # 18/15 = 20% above median → CARO (15–30% band)
        hist = self._hist([15.0, 15.0, 15.0], "l")
        result = classify_new_item_price({"precio_unitario": 18.0, "unidad": "l"}, hist)
        assert result["clasificacion"] == "CARO"

    def test_no_unit_check_when_hist_unit_empty(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        # If historic has no unit, allow comparison (backward compat)
        hist = self._hist([100.0, 100.0, 100.0], "")
        result = classify_new_item_price({"precio_unitario": 110.0, "unidad": "m²"}, hist)
        assert result["clasificacion"] == "NORMAL"

    def test_sin_precio_has_unidad(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        result = classify_new_item_price({"precio_unitario": None, "unidad": "t"}, None)
        assert result["unidad"] == "t"

    def test_primera_muestra_has_unidad(self):
        from src.ratios.item_ratio_calculator import classify_new_item_price
        result = classify_new_item_price({"precio_unitario": 950.0, "unidad": "t"}, None)
        assert result["unidad"] == "t"

    # --- DB: ItemInstance stores unidad ---

    def test_item_instance_stores_unidad(self, db_session):
        from datetime import datetime, timezone
        from src.db.schema import Budget, ItemInstance, ItemMaster
        budget = Budget(filename="b.Presto", file_hash="zz001", source_format="presto", total_cost=1000.0)
        db_session.add(budget)
        db_session.flush()

        master = ItemMaster(item_key="acero b500s|t", categoria="ESTRUCTURA", unidad="t", muestras_count=0)
        db_session.add(master)
        db_session.flush()

        inst = ItemInstance(
            budget_id=budget.id,
            item_master_id=master.id,
            descripcion="Acero B-500S",
            unidad="t",
            cantidad=12.0,
            precio_unitario=950.0,
            precio_total=11400.0,
            validation_status="VALID",
        )
        db_session.add(inst)
        db_session.commit()

        fetched = db_session.get(ItemInstance, inst.id)
        assert fetched.unidad == "t"

    # --- get_item_ratio_history propagates unidad ---

    def test_get_item_ratio_history_returns_unidad(self, db_session):
        from datetime import datetime, timezone
        from src.db.schema import Budget, ItemInstance, ItemMaster
        from src.ratios.item_ratio_calculator import get_item_ratio_history

        budget = Budget(filename="c.Presto", file_hash="zz002", source_format="presto", total_cost=5000.0)
        db_session.add(budget)
        db_session.flush()

        master = ItemMaster(item_key="hormigon ha30|m3", categoria="ESTRUCTURA", unidad="m3", muestras_count=0)
        db_session.add(master)
        db_session.flush()

        for price in [180.0, 185.0, 190.0]:
            db_session.add(ItemInstance(
                budget_id=budget.id,
                item_master_id=master.id,
                descripcion="Hormigón HA-30",
                unidad="m3",
                precio_unitario=price,
                precio_total=price * 10,
                validation_status="VALID",
            ))
        db_session.commit()

        stats = get_item_ratio_history(db_session, master.id)
        assert stats is not None
        assert stats["unidad"] == "m3"
        assert stats["mediana"] == pytest.approx(185.0, abs=0.01)

    # --- Different units create separate ItemMaster records ---

    def test_different_units_create_separate_masters(self, db_session):
        from src.db.schema import ItemMaster
        from src.core.item_extractor import make_item_key

        key_m3 = make_item_key("Hormigón", "m³")
        key_kg = make_item_key("Hormigón", "kg")

        m1 = ItemMaster(item_key=key_m3, categoria="ESTRUCTURA", unidad="m³", muestras_count=0)
        m2 = ItemMaster(item_key=key_kg, categoria="ESTRUCTURA", unidad="kg", muestras_count=0)
        db_session.add_all([m1, m2])
        db_session.commit()

        masters = db_session.query(ItemMaster).filter(
            ItemMaster.item_key.in_([key_m3, key_kg])
        ).all()
        assert len(masters) == 2
        units = {m.unidad for m in masters}
        assert "m³" in units
        assert "kg" in units

    # --- Non-m² items produce correct ratios ---

    def test_acero_ratio_per_ton(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {
            "source_format": "bc3",
            "chapters": [
                {
                    "chapter_code": "E01",
                    "chapter_name": "Acero B-500S",
                    "total_cost": 11400.0,
                    "quantity": 12.0,
                    "unit": "t",
                    "unit_cost": 950.0,
                }
            ],
            "errors": [],
            "warnings": [],
        }
        items = extract_items_from_budget(budget)
        assert len(items) == 1
        assert items[0]["unidad"] == "t"
        assert items[0]["precio_unitario"] == pytest.approx(950.0, abs=0.01)

    def test_pintura_ratio_per_litre(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {
            "source_format": "bc3",
            "chapters": [
                {
                    "chapter_code": "A01",
                    "chapter_name": "Pintura plástica",
                    "total_cost": 7500.0,
                    "quantity": 500.0,
                    "unit": "l",
                    "unit_cost": 15.0,
                }
            ],
            "errors": [],
            "warnings": [],
        }
        items = extract_items_from_budget(budget)
        assert items[0]["unidad"] == "l"
        assert items[0]["precio_unitario"] == pytest.approx(15.0, abs=0.01)

    def test_puerta_ratio_per_ud(self):
        from src.core.item_extractor import extract_items_from_budget
        budget = {
            "source_format": "bc3",
            "chapters": [
                {
                    "chapter_code": "C01",
                    "chapter_name": "Puerta interior",
                    "total_cost": 3600.0,
                    "quantity": 3.0,
                    "unit": "ud",
                    "unit_cost": 1200.0,
                }
            ],
            "errors": [],
            "warnings": [],
        }
        items = extract_items_from_budget(budget)
        assert items[0]["unidad"] == "ud"
        assert items[0]["precio_unitario"] == pytest.approx(1200.0, abs=0.01)

    # --- crud: response includes unidad_medida ---

    def test_master_to_dict_has_unidad_medida(self, db_session):
        from src.db.schema import ItemMaster
        from app.crud.items import _master_to_dict
        master = ItemMaster(item_key="x|m3", categoria="ESTRUCTURA", unidad="m3", muestras_count=0)
        db_session.add(master)
        db_session.commit()
        d = _master_to_dict(master)
        assert "unidad_medida" in d
        assert d["unidad_medida"] == "€/m3"

    def test_master_to_dict_fallback_unidad(self, db_session):
        from src.db.schema import ItemMaster
        from app.crud.items import _master_to_dict
        master = ItemMaster(item_key="y|", categoria="OTROS", unidad=None, muestras_count=0)
        db_session.add(master)
        db_session.commit()
        d = _master_to_dict(master)
        assert d["unidad_medida"] == "€/ud"
