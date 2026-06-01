"""Tests for clasificacion_service and item_master_ratios CRUD."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.item_master_ratios import (
    get_median_prices_por_categoria,
    get_or_create_ratio,
    get_ratio_by_categoria,
    get_ratios_por_item,
    update_ratio_incremental,
)
from app.services.clasificacion_service import (
    calcular_confianza_basada_en_n,
    clasificar_item_desde_descripcion,
    determinar_categoria_por_precio,
)
from src.db.schema import Base, Budget, Categoria, Confianza, ItemMaster, ItemMasterRatio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def item_master(db_session):
    item = ItemMaster(item_key="test_item_001", categoria_asignada="MEDIUM")
    db_session.add(item)
    db_session.commit()
    return item


_RATIOS = {"MEDIUM": 150.0, "PREMIUM": 300.0, "LUXURY": 500.0, "LUXURY_PLUS": 800.0}


# ---------------------------------------------------------------------------
# Suite 1: Clasificación por keywords
# ---------------------------------------------------------------------------

def test_clasificar_carpinteria_premium():
    result = clasificar_item_desde_descripcion("Carpintería doble acristalamiento")
    assert result == Categoria.PREMIUM


def test_clasificar_carpinteria_luxury_plus():
    result = clasificar_item_desde_descripcion("Carpintería madera maciza motorizada")
    assert result == Categoria.LUXURY_PLUS


def test_clasificar_presupuesto_basico():
    result = clasificar_item_desde_descripcion("Solución funcional económica")
    assert result == Categoria.MEDIUM


def test_clasificar_gran_formato_luxury():
    result = clasificar_item_desde_descripcion("Suelo porcelánico gran formato 120x120")
    assert result == Categoria.LUXURY


def test_clasificar_puerta_motorizada_luxury_plus():
    result = clasificar_item_desde_descripcion("Puerta blindada motorizada con automatismo")
    assert result == Categoria.LUXURY_PLUS


def test_clasificar_pintura_plastica_medium():
    result = clasificar_item_desde_descripcion("Pintura plástica mate acabado liso")
    assert result == Categoria.MEDIUM


def test_clasificar_tarima_roble_premium():
    result = clasificar_item_desde_descripcion("Tarima de roble flotante barnizada")
    assert result == Categoria.PREMIUM


def test_clasificar_aluminio_lacado_premium():
    result = clasificar_item_desde_descripcion("Ventana aluminio lacado RPT doble vidrio")
    assert result == Categoria.PREMIUM


def test_clasificar_marmol_luxury_plus():
    result = clasificar_item_desde_descripcion("Encimera mármol Carrara pulida")
    assert result == Categoria.LUXURY_PLUS


def test_clasificar_madera_maciza_luxury():
    result = clasificar_item_desde_descripcion("Puerta de madera maciza lacada")
    assert result == Categoria.LUXURY


def test_clasificar_azulejo_medium():
    result = clasificar_item_desde_descripcion("Azulejo metro cocina 10x20 blanco")
    assert result == Categoria.MEDIUM


def test_clasificar_descripcion_vacia_retorna_medium():
    assert clasificar_item_desde_descripcion("") == Categoria.MEDIUM
    assert clasificar_item_desde_descripcion("   ") == Categoria.MEDIUM


def test_clasificar_none_retorna_medium():
    # mypy: None is not str, but we guard against bad callers
    result = clasificar_item_desde_descripcion(None)  # type: ignore[arg-type]
    assert result == Categoria.MEDIUM


# ---------------------------------------------------------------------------
# Suite 2: Fallback por precio
# ---------------------------------------------------------------------------

def test_fallback_precio_bajo():
    """Precio muy por debajo de MEDIUM → MEDIUM."""
    result = determinar_categoria_por_precio(80.0, _RATIOS)
    assert result == Categoria.MEDIUM


def test_fallback_precio_alto():
    """Precio por encima de LUXURY_PLUS → LUXURY_PLUS."""
    result = determinar_categoria_por_precio(1000.0, _RATIOS)
    assert result == Categoria.LUXURY_PLUS


def test_fallback_precio_intermedio_premium():
    """270 EUR: gap to PREMIUM (30) < gap to MEDIUM (120) → PREMIUM."""
    result = determinar_categoria_por_precio(270.0, _RATIOS)
    assert result == Categoria.PREMIUM


def test_fallback_precio_intermedio_luxury():
    """420 EUR: gap to LUXURY (80) < gap to PREMIUM (120) → LUXURY."""
    result = determinar_categoria_por_precio(420.0, _RATIOS)
    assert result == Categoria.LUXURY


def test_fallback_ratios_vacios_retorna_medium():
    result = determinar_categoria_por_precio(500.0, {})
    assert result == Categoria.MEDIUM


def test_fallback_ratios_sin_categorias_validas_retorna_medium():
    result = determinar_categoria_por_precio(500.0, {"DESCONOCIDA": 400.0})
    assert result == Categoria.MEDIUM


def test_clasificar_sin_keywords_sin_precio_retorna_medium():
    result = clasificar_item_desde_descripcion("Partida sin descripcion conocida")
    assert result == Categoria.MEDIUM


def test_clasificar_sin_keywords_con_precio_usa_fallback():
    result = clasificar_item_desde_descripcion(
        "Partida sin descripcion conocida",
        precio_unitario=270.0,
        ratios_historicos=_RATIOS,
    )
    assert result == Categoria.PREMIUM


def test_clasificar_sin_keywords_precio_sin_ratios_retorna_medium():
    result = clasificar_item_desde_descripcion(
        "Partida sin descripcion conocida",
        precio_unitario=270.0,
        ratios_historicos=None,
    )
    assert result == Categoria.MEDIUM


# ---------------------------------------------------------------------------
# Suite 3: Cálculo de confianza
# ---------------------------------------------------------------------------

def test_confianza_n0_muy_debil():
    assert calcular_confianza_basada_en_n(0) == Confianza.MUY_DEBIL


def test_confianza_n1_muy_debil():
    assert calcular_confianza_basada_en_n(1) == Confianza.MUY_DEBIL


def test_confianza_n2_debil():
    assert calcular_confianza_basada_en_n(2) == Confianza.DEBIL


def test_confianza_n4_debil():
    assert calcular_confianza_basada_en_n(4) == Confianza.DEBIL


def test_confianza_n5_solido():
    assert calcular_confianza_basada_en_n(5) == Confianza.SOLIDO


def test_confianza_n9_solido():
    assert calcular_confianza_basada_en_n(9) == Confianza.SOLIDO


def test_confianza_n10_muy_solido():
    assert calcular_confianza_basada_en_n(10) == Confianza.MUY_SOLIDO


def test_confianza_n100_muy_solido():
    assert calcular_confianza_basada_en_n(100) == Confianza.MUY_SOLIDO


# ---------------------------------------------------------------------------
# Suite 4: CRUD ItemMasterRatio (integración con BD)
# ---------------------------------------------------------------------------

def test_get_or_create_nuevo(db_session, item_master):
    ratio = get_or_create_ratio(db_session, item_master.id, "PREMIUM")
    assert ratio.id is not None
    assert ratio.item_master_id == item_master.id
    assert ratio.categoria == "PREMIUM"
    assert ratio.ratio_actual is None
    assert ratio.muestras_count == 0
    assert ratio.confianza == Confianza.MUY_DEBIL


def test_get_or_create_existente(db_session, item_master):
    ratio1 = get_or_create_ratio(db_session, item_master.id, "LUXURY")
    ratio2 = get_or_create_ratio(db_session, item_master.id, "LUXURY")
    assert ratio1.id == ratio2.id


def test_update_ratio_primera_muestra(db_session, item_master):
    ratio = update_ratio_incremental(db_session, item_master.id, "MEDIUM", 200.0)
    assert ratio.ratio_actual == 200.0
    assert ratio.mediana == 200.0
    assert ratio.min_valor == 200.0
    assert ratio.max_valor == 200.0
    assert ratio.muestras_count == 1


def test_update_ratio_segunda_muestra(db_session, item_master):
    update_ratio_incremental(db_session, item_master.id, "MEDIUM", 200.0)
    ratio = update_ratio_incremental(db_session, item_master.id, "MEDIUM", 300.0)
    # Running avg: (200*1 + 300) / 2 = 250
    assert ratio.ratio_actual == pytest.approx(250.0)
    assert ratio.min_valor == pytest.approx(200.0)
    assert ratio.max_valor == pytest.approx(300.0)
    assert ratio.muestras_count == 2


def test_update_ratio_confianza_sube(db_session, item_master):
    for i in range(10):
        ratio = update_ratio_incremental(db_session, item_master.id, "LUXURY", float(i * 100))

    assert ratio.muestras_count == 10
    assert ratio.confianza == Confianza.MUY_SOLIDO


def test_update_ratio_confianza_progression(db_session, item_master):
    r = update_ratio_incremental(db_session, item_master.id, "PREMIUM", 300.0)
    assert r.confianza == Confianza.MUY_DEBIL  # N=1

    r = update_ratio_incremental(db_session, item_master.id, "PREMIUM", 320.0)
    assert r.confianza == Confianza.DEBIL  # N=2

    for _ in range(3):
        r = update_ratio_incremental(db_session, item_master.id, "PREMIUM", 310.0)
    assert r.confianza == Confianza.SOLIDO  # N=5


def test_get_ratio_by_categoria_encontrado(db_session, item_master):
    update_ratio_incremental(db_session, item_master.id, "LUXURY_PLUS", 900.0)
    result = get_ratio_by_categoria(db_session, item_master.id, "LUXURY_PLUS")
    assert result is not None
    assert result.ratio_actual == pytest.approx(900.0)


def test_get_ratio_by_categoria_no_encontrado(db_session, item_master):
    result = get_ratio_by_categoria(db_session, item_master.id, "LUXURY")
    assert result is None


def test_get_ratios_por_item_vacio(db_session, item_master):
    result = get_ratios_por_item(db_session, item_master.id)
    assert result == []


def test_get_ratios_por_item_multiples_categorias(db_session, item_master):
    for cat in ["MEDIUM", "PREMIUM", "LUXURY"]:
        update_ratio_incremental(db_session, item_master.id, cat, 100.0)

    result = get_ratios_por_item(db_session, item_master.id)
    assert len(result) == 3
    assert {r.categoria for r in result} == {"MEDIUM", "PREMIUM", "LUXURY"}


def test_get_median_prices_sin_datos_usa_defaults(db_session):
    result = get_median_prices_por_categoria(db_session)
    assert result["MEDIUM"] == pytest.approx(150.0)
    assert result["PREMIUM"] == pytest.approx(300.0)
    assert result["LUXURY"] == pytest.approx(500.0)
    assert result["LUXURY_PLUS"] == pytest.approx(800.0)


def test_get_median_prices_con_datos(db_session):
    item = ItemMaster(item_key="test_medians", categoria_asignada="PREMIUM")
    db_session.add(item)
    db_session.commit()

    # Create two PREMIUM ratios with different medians; avg = (200+400)/2 = 300
    db_session.add(ItemMasterRatio(
        item_master_id=item.id, categoria="PREMIUM",
        mediana=200.0, muestras_count=1, confianza="MUY_DÉBIL",
        ultima_actualizacion=__import__("datetime").datetime.now(),
    ))
    db_session.add(ItemMasterRatio(
        item_master_id=item.id, categoria="LUXURY",
        mediana=600.0, muestras_count=1, confianza="MUY_DÉBIL",
        ultima_actualizacion=__import__("datetime").datetime.now(),
    ))
    db_session.commit()

    result = get_median_prices_por_categoria(db_session)
    assert result["PREMIUM"] == pytest.approx(200.0)
    assert result["LUXURY"] == pytest.approx(600.0)
    # MEDIUM and LUXURY_PLUS not in DB → keep defaults
    assert result["MEDIUM"] == pytest.approx(150.0)
    assert result["LUXURY_PLUS"] == pytest.approx(800.0)


def test_cascade_delete_item_master(db_session, item_master):
    update_ratio_incremental(db_session, item_master.id, "MEDIUM", 200.0)
    db_session.commit()

    db_session.delete(item_master)
    db_session.commit()

    remaining = db_session.query(ItemMasterRatio).filter_by(item_master_id=item_master.id).count()
    assert remaining == 0
