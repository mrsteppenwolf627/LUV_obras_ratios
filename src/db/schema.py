"""SQLAlchemy ORM models for the LUV Obras Ratios system."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship, validates


class Categoria(str, PyEnum):
    """Categoría de gama LUV Studio."""

    MEDIUM = "MEDIUM"
    PREMIUM = "PREMIUM"
    LUXURY = "LUXURY"
    LUXURY_PLUS = "LUXURY_PLUS"


class Confianza(str, PyEnum):
    """Nivel de confianza del ratio basado en muestras."""

    MUY_DEBIL = "MUY_DÉBIL"   # N < 2
    DEBIL = "DÉBIL"            # 2 ≤ N < 5
    SOLIDO = "SÓLIDO"          # 5 ≤ N < 10
    MUY_SOLIDO = "MUY_SÓLIDO"  # N ≥ 10


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Budget(Base):
    """One imported budget file."""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)
    import_date = Column(DateTime, default=_utcnow, nullable=False)
    surface_m2 = Column(Float, nullable=True)
    building_type = Column(String(100), nullable=True)
    source_format = Column(String(20), nullable=False)  # 'excel' | 'bc3'
    total_cost = Column(Float, nullable=True)
    raw_data_json = Column(Text, nullable=True)

    items = relationship("LineItem", back_populates="budget", cascade="all, delete-orphan")
    space_ratios = relationship("SpaceRatio", back_populates="budget", cascade="all, delete-orphan")
    item_instances = relationship("ItemInstance", back_populates="budget", cascade="all, delete-orphan")
    validation_logs = relationship(
        "ValidationLog",
        primaryjoin="ValidationLog.budget_id == Budget.id",
        back_populates="budget",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Budget id={self.id} filename={self.filename!r} hash={self.file_hash[:8]}>"


class LineItem(Base):
    """A single chapter/line extracted from a budget."""

    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    chapter_code = Column(String(100), nullable=True)
    chapter_name = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(30), nullable=True)
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    # VALID | DUBIOUS | EXCLUDED
    validation_status = Column(String(20), nullable=False, default="VALID")

    budget = relationship("Budget", back_populates="items")
    validation_logs = relationship(
        "ValidationLog",
        primaryjoin="ValidationLog.line_item_id == LineItem.id",
        back_populates="line_item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LineItem id={self.id} chapter={self.chapter_code!r} total={self.total_cost}>"


class Ratio(Base):
    """Aggregated ratio per chapter, optionally per building type."""

    __tablename__ = "ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_code = Column(String(100), nullable=False)
    chapter_name = Column(String(500), nullable=True)
    building_type = Column(String(100), nullable=True)
    cost_per_m2 = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    percentil_25 = Column(Float, nullable=True)
    percentil_75 = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    sample_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("chapter_code", "building_type", name="uq_ratio_chapter_type"),
    )

    def __repr__(self) -> str:
        return f"<Ratio chapter={self.chapter_code!r} median={self.median} n={self.sample_count}>"


class SpaceRatio(Base):
    """Per-space cost ratio extracted from a Presto budget."""

    __tablename__ = "space_ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    nombre = Column(String(200), nullable=False)
    zona = Column(String(100), nullable=True)
    coste = Column(Float, nullable=True)
    m2 = Column(Float, default=0.0)
    ratio_eur_m2 = Column(Float, nullable=True)
    coste_prorrateado = Column(Float, nullable=True)
    import_date = Column(DateTime, default=_utcnow, nullable=False)

    budget = relationship("Budget", back_populates="space_ratios")

    def __repr__(self) -> str:
        return f"<SpaceRatio nombre={self.nombre!r} coste={self.coste} m2={self.m2}>"


class ItemMaster(Base):
    """Deduplicated catalogue of unique items across all budgets."""

    __tablename__ = "item_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_key = Column(String(500), unique=True, nullable=False)
    categoria = Column(String(100), nullable=True)
    subcategoria = Column(String(100), nullable=True)
    unidad = Column(String(50), nullable=True)

    mediana_unitario = Column(Float, nullable=True)
    media_unitario = Column(Float, nullable=True)
    min_unitario = Column(Float, nullable=True)
    max_unitario = Column(Float, nullable=True)
    desv_std = Column(Float, nullable=True)
    muestras_count = Column(Integer, default=0)

    primera_fecha = Column(DateTime, nullable=True)
    ultima_fecha = Column(DateTime, nullable=True)
    ultima_actualizacion = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    categoria_asignada = Column(String(20), nullable=False, default="MEDIUM")
    gama_asignada = Column(String(20), nullable=False, default="SIN_CLASIFICAR")

    instances = relationship(
        "ItemInstance", back_populates="item_master", cascade="all, delete-orphan"
    )
    ratios_por_categoria = relationship(
        "ItemMasterRatio",
        back_populates="item_master",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ItemMaster key={self.item_key!r} cat={self.categoria!r} n={self.muestras_count}>"


class ItemMasterRatio(Base):
    """Ratio histórico de un item para una categoría específica."""

    __tablename__ = "item_master_ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_master_id = Column(Integer, ForeignKey("item_master.id"), nullable=False)
    categoria = Column(String(20), nullable=False)

    ratio_actual = Column(Float, nullable=True)
    mediana = Column(Float, nullable=True)
    min_valor = Column(Float, nullable=True)
    max_valor = Column(Float, nullable=True)
    desv_std = Column(Float, nullable=True)
    percentil_25 = Column(Float, nullable=True)
    percentil_75 = Column(Float, nullable=True)

    muestras_count = Column(Integer, default=0)
    confianza = Column(String(20), default="MUY_DÉBIL")
    ultima_actualizacion = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    item_master = relationship("ItemMaster", back_populates="ratios_por_categoria")

    __table_args__ = (
        UniqueConstraint("item_master_id", "categoria", name="uq_item_cat_ratio"),
    )

    def __repr__(self) -> str:
        return f"<ItemMasterRatio item={self.item_master_id} cat={self.categoria} ratio={self.ratio_actual} n={self.muestras_count}>"


class ItemInstance(Base):
    """One occurrence of an item inside a specific budget."""

    __tablename__ = "item_instance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    item_master_id = Column(Integer, ForeignKey("item_master.id"), nullable=False)

    codigo = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=True)
    categoria_original = Column(String(200), nullable=True)
    unidad = Column(String(50), nullable=True)
    cantidad = Column(Float, nullable=True)
    precio_unitario = Column(Float, nullable=True)
    precio_total = Column(Float, nullable=True)

    categoria_detectada = Column(String(100), nullable=True)
    confianza_clasificacion = Column(Float, nullable=True)
    desviacion_vs_historico = Column(Float, nullable=True)
    clasificacion_precio = Column(String(50), nullable=True)

    categoria_asignada = Column(String(20), nullable=False, default="MEDIUM")
    ratio_comparativa = Column(Float, nullable=True)

    validation_status = Column(String(20), nullable=False, default="VALID")
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    budget = relationship("Budget", back_populates="item_instances")
    item_master = relationship("ItemMaster", back_populates="instances")

    def __repr__(self) -> str:
        return (
            f"<ItemInstance id={self.id} master={self.item_master_id} "
            f"precio={self.precio_unitario} status={self.clasificacion_precio!r}>"
        )


class BudgetImport(Base):
    """Metadata record for each JSON-API budget import."""

    __tablename__ = "budget_imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)
    building_type = Column(String(100), nullable=True)
    import_date = Column(DateTime, default=_utcnow, nullable=False)
    # Technical ingestion state: success | partial | error
    status = Column(String(50), nullable=False, default="success")
    items_count = Column(Integer, nullable=True)
    error_message = Column(String(1000), nullable=True)

    # FASE MASTER — functional approval workflow (separate from technical status above)
    # Values: PENDING_REVIEW | APPROVED | REJECTED
    approval_status = Column(String(30), nullable=False, default="PENDING_REVIEW")
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BudgetImport id={self.id} hash={self.file_hash[:8]} "
            f"status={self.status!r} approval={self.approval_status!r}>"
        )


class ValidationLog(Base):
    """One validation event tied to a budget or a specific line item."""

    __tablename__ = "validation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_item_id = Column(Integer, ForeignKey("line_items.id"), nullable=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    rule_name = Column(String(100), nullable=False)
    # PASS | FAIL | WARNING
    status = Column(String(20), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    line_item = relationship(
        "LineItem",
        primaryjoin="ValidationLog.line_item_id == LineItem.id",
        back_populates="validation_logs",
    )
    budget = relationship(
        "Budget",
        primaryjoin="ValidationLog.budget_id == Budget.id",
        back_populates="validation_logs",
    )

    def __repr__(self) -> str:
        return f"<ValidationLog rule={self.rule_name!r} status={self.status!r}>"


class GamaRange(Base):
    """Material price ranges organized by luxury tier (medium/premium/luxury/luxury_plus)."""

    __tablename__ = "gama_ranges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_type = Column(String(100), nullable=False)
    categoria = Column(String(100), nullable=False)

    medium_min = Column(Float, nullable=True)
    medium_max = Column(Float, nullable=True)

    premium_min = Column(Float, nullable=True)
    premium_max = Column(Float, nullable=True)

    luxury_min = Column(Float, nullable=True)
    luxury_max = Column(Float, nullable=True)

    luxury_plus_min = Column(Float, nullable=True)
    luxury_plus_max = Column(Float, nullable=True)

    fuente = Column(String(255), nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("material_type", "categoria", name="uq_gama_material_categoria"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_constraints()

    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if name in (
            "medium_min",
            "medium_max",
            "premium_min",
            "premium_max",
            "luxury_min",
            "luxury_max",
            "luxury_plus_min",
            "luxury_plus_max",
        ):
            self._validate_constraints()

    def _validate_constraints(self) -> None:
        """Validate all tier constraints."""
        # MEDIUM tier: min <= max
        if self.medium_min is not None and self.medium_max is not None:
            if self.medium_min > self.medium_max:
                raise ValueError(
                    f"MEDIUM tier constraint violated: "
                    f"medium_min ({self.medium_min}) must be <= medium_max ({self.medium_max})"
                )

        # PREMIUM tier: min <= max, and min >= medium_max (no inversion)
        if self.premium_min is not None and self.premium_max is not None:
            if self.premium_min > self.premium_max:
                raise ValueError(
                    f"PREMIUM tier constraint violated: "
                    f"premium_min ({self.premium_min}) must be <= premium_max ({self.premium_max})"
                )
        if self.premium_min is not None and self.medium_max is not None:
            if self.premium_min < self.medium_max:
                raise ValueError(
                    f"PREMIUM tier constraint violated: "
                    f"premium_min ({self.premium_min}) should be >= medium_max ({self.medium_max}) "
                    f"to avoid tier overlap"
                )

        # LUXURY tier: min <= max, and min >= premium_max
        if self.luxury_min is not None and self.luxury_max is not None:
            if self.luxury_min > self.luxury_max:
                raise ValueError(
                    f"LUXURY tier constraint violated: "
                    f"luxury_min ({self.luxury_min}) must be <= luxury_max ({self.luxury_max})"
                )
        if self.luxury_min is not None and self.premium_max is not None:
            if self.luxury_min < self.premium_max:
                raise ValueError(
                    f"LUXURY tier constraint violated: "
                    f"luxury_min ({self.luxury_min}) should be >= premium_max ({self.premium_max}) "
                    f"to avoid tier overlap"
                )

        # LUXURY_PLUS tier: min <= max, and min >= luxury_max
        if self.luxury_plus_min is not None and self.luxury_plus_max is not None:
            if self.luxury_plus_min > self.luxury_plus_max:
                raise ValueError(
                    f"LUXURY_PLUS tier constraint violated: "
                    f"luxury_plus_min ({self.luxury_plus_min}) must be <= luxury_plus_max ({self.luxury_plus_max})"
                )
        if self.luxury_plus_min is not None and self.luxury_max is not None:
            if self.luxury_plus_min < self.luxury_max:
                raise ValueError(
                    f"LUXURY_PLUS tier constraint violated: "
                    f"luxury_plus_min ({self.luxury_plus_min}) should be >= luxury_max ({self.luxury_max}) "
                    f"to avoid tier overlap"
                )

    def __repr__(self) -> str:
        return f"<GamaRange material={self.material_type!r} cat={self.categoria!r}>"
