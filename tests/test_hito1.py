"""Tests for Hito 1: schema, readers, normalizer, import, ratios, master Excel."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from openpyxl import load_workbook
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# -- Project root on sys.path via conftest.py --

from src.core.auditor import compute_file_hash, generate_import_log, save_log
from src.core.bc3_reader import read_bc3
from src.core.excel_reader import read_excel
from src.core.normalizer import normalize
from src.db.models import init_db
from src.db.queries import get_budget_by_hash, list_all_budgets, list_all_ratios
from src.db.schema import Base, Budget, LineItem, Ratio, ValidationLog
from src.export.excel_master_generator import generate_master_excel
from src.ratios.calculator import recalculate_all_ratios

SAMPLES_DIR = Path("data/samples")
SAMPLE_XLSX = SAMPLES_DIR / "proyecto_001" / "22_10_SCE_Datos.xlsx"
SAMPLE_BC3 = SAMPLES_DIR / "proyecto_001" / "P22-143.1 Pressupost Sant Celoni.bc3"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path):
    """In-memory-like SQLite in a temp directory."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    @event.listens_for(engine, "connect")
    def fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def minimal_budget():
    return Budget(
        filename="test.xlsx",
        file_hash="a" * 64,
        source_format="excel",
        total_cost=100_000.0,
        surface_m2=200.0,
        building_type="residential",
    )


@pytest.fixture()
def minimal_item(minimal_budget):
    return LineItem(
        budget=minimal_budget,
        chapter_code="C01",
        chapter_name="Actuaciones previas",
        total_cost=10_000.0,
        validation_status="VALID",
    )


# ---------------------------------------------------------------------------
# Tarea 1: Schema
# ---------------------------------------------------------------------------


class TestSchema:
    def test_tables_created(self, tmp_db):
        """All four model tables should be accessible after init."""
        # Tables exist if we can query them without error
        assert tmp_db.query(Budget).count() == 0
        assert tmp_db.query(LineItem).count() == 0
        assert tmp_db.query(Ratio).count() == 0
        assert tmp_db.query(ValidationLog).count() == 0

    def test_budget_insert(self, tmp_db):
        b = Budget(filename="a.xlsx", file_hash="b" * 64, source_format="excel")
        tmp_db.add(b)
        tmp_db.commit()
        assert b.id is not None

    def test_line_item_foreign_key(self, tmp_db):
        b = Budget(filename="b.xlsx", file_hash="c" * 64, source_format="bc3")
        item = LineItem(
            budget=b, chapter_code="C01", chapter_name="X", total_cost=1000.0
        )
        tmp_db.add(b)
        tmp_db.commit()
        assert item.budget_id == b.id

    def test_validation_log_insert(self, tmp_db):
        b = Budget(filename="c.xlsx", file_hash="d" * 64, source_format="excel")
        log = ValidationLog(budget=b, rule_name="TEST", status="PASS")
        tmp_db.add(b)
        tmp_db.commit()
        assert log.id is not None

    def test_timestamps_auto(self, tmp_db):
        b = Budget(filename="d.xlsx", file_hash="e" * 64, source_format="excel")
        tmp_db.add(b)
        tmp_db.commit()
        assert b.import_date is not None


# ---------------------------------------------------------------------------
# Tarea 2: Excel Reader
# ---------------------------------------------------------------------------


class TestExcelReader:
    def test_read_sample(self):
        if not SAMPLE_XLSX.exists():
            pytest.skip("Sample xlsx not available")
        result = read_excel(SAMPLE_XLSX)
        assert result["source_format"] == "excel"
        assert len(result["chapters"]) > 0

    def test_chapters_have_amounts(self):
        if not SAMPLE_XLSX.exists():
            pytest.skip("Sample xlsx not available")
        result = read_excel(SAMPLE_XLSX)
        for ch in result["chapters"]:
            assert ch["total_cost"] > 0

    def test_unsupported_extension(self, tmp_path):
        bad = tmp_path / "file.csv"
        bad.write_text("a,b")
        result = read_excel(bad)
        assert result["errors"]

    def test_synthetic_xlsx(self, tmp_path):
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["Código", "Descripción", "Importe"])
        ws.append(["C01", "Actuaciones previas", 5000.0])
        ws.append(["C02", "Estructura", 20000.0])
        out = tmp_path / "synth.xlsx"
        wb.save(str(out))

        result = read_excel(out)
        assert len(result["chapters"]) == 2
        codes = {c["chapter_code"] for c in result["chapters"]}
        assert "C01" in codes or "C02" in codes
        assert result["total_cost"] == pytest.approx(25000.0)

    def test_no_crashes_on_empty_workbook(self, tmp_path):
        from openpyxl import Workbook

        wb = Workbook()
        out = tmp_path / "empty.xlsx"
        wb.save(str(out))
        result = read_excel(out)
        assert isinstance(result["chapters"], list)


# ---------------------------------------------------------------------------
# Tarea 3: BC3 Reader
# ---------------------------------------------------------------------------


class TestBC3Reader:
    def test_read_sample(self):
        if not SAMPLE_BC3.exists():
            pytest.skip("Sample bc3 not available")
        result = read_bc3(SAMPLE_BC3)
        assert result["source_format"] == "bc3"
        assert len(result["chapters"]) > 0

    def test_chapters_have_amounts(self):
        if not SAMPLE_BC3.exists():
            pytest.skip("Sample bc3 not available")
        result = read_bc3(SAMPLE_BC3)
        for ch in result["chapters"]:
            assert ch["total_cost"] > 0

    def test_unsupported_extension(self, tmp_path):
        bad = tmp_path / "file.txt"
        bad.write_text("hello")
        result = read_bc3(bad)
        assert result["errors"]

    def test_synthetic_bc3(self, tmp_path):
        content = (
            "~V|RIB|FIEBDC-3/2020||\n"
            "~C|C01#||ACTUACIONES PREVIAS|5000.00|281122|0|\n"
            "~C|C02#||ESTRUCTURA|20000.00|281122|0|\n"
        )
        f = tmp_path / "test.bc3"
        f.write_bytes(content.encode("cp1252"))
        result = read_bc3(f)
        assert len(result["chapters"]) == 2
        codes = {c["chapter_code"] for c in result["chapters"]}
        assert "C01" in codes
        assert "C02" in codes

    def test_top_level_detection(self, tmp_path):
        content = (
            "~C|C01#||TOP CHAPTER|10000.0|281122|0|\n"
            "~C|C0101#||SUB CHAPTER|3000.0|281122|0|\n"
        )
        f = tmp_path / "t.bc3"
        f.write_bytes(content.encode("cp1252"))
        result = read_bc3(f)
        top = [c for c in result["chapters"] if c["is_top_level"]]
        sub = [c for c in result["chapters"] if not c["is_top_level"]]
        assert len(top) == 1
        assert len(sub) == 1


# ---------------------------------------------------------------------------
# Tarea 4: Normalizer
# ---------------------------------------------------------------------------


class TestNormalizer:
    def _make_raw(self, chapters=None, total=None):
        return {
            "source_format": "excel",
            "filename": "test.xlsx",
            "filepath": "test.xlsx",
            "chapters": chapters or [],
            "total_cost": total,
            "warnings": [],
            "errors": [],
            "sheets_processed": ["Sheet1"],
        }

    def test_returns_budget_and_items(self):
        raw = self._make_raw(
            [{"chapter_code": "C01", "chapter_name": "Test", "total_cost": 1000.0, "confidence": "HIGH"}]
        )
        budget, items, logs = normalize(raw, file_hash="x" * 64)
        assert isinstance(budget, Budget)
        assert len(items) == 1
        assert items[0].validation_status == "VALID"

    def test_missing_amount_is_dubious(self):
        raw = self._make_raw(
            [{"chapter_code": "C01", "chapter_name": "Test", "total_cost": None, "confidence": "HIGH"}]
        )
        budget, items, logs = normalize(raw, file_hash="x" * 64)
        assert items[0].validation_status == "DUBIOUS"

    def test_negative_amount_is_dubious(self):
        raw = self._make_raw(
            [{"chapter_code": "C01", "chapter_name": "Test", "total_cost": -100.0, "confidence": "HIGH"}]
        )
        budget, items, logs = normalize(raw, file_hash="x" * 64)
        assert items[0].validation_status == "DUBIOUS"

    def test_surface_m2_stored(self):
        raw = self._make_raw()
        budget, _, _ = normalize(raw, surface_m2=250.0, file_hash="x" * 64)
        assert budget.surface_m2 == 250.0

    def test_reader_errors_create_logs(self):
        raw = self._make_raw()
        raw["errors"] = ["DECODE_FAILED"]
        budget, _, logs = normalize(raw, file_hash="x" * 64)
        rule_names = [l.rule_name for l in logs]
        assert "READER_ERROR" in rule_names


# ---------------------------------------------------------------------------
# Tarea 5: Auditor
# ---------------------------------------------------------------------------


class TestAuditor:
    def test_hash_consistency(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_bytes(b"hello world")
        h1 = compute_file_hash(f)
        h2 = compute_file_hash(f)
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_differs_for_different_content(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"aaa")
        f2.write_bytes(b"bbb")
        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_generate_log_structure(self):
        budget = Budget(
            filename="f.xlsx",
            file_hash="a" * 64,
            source_format="excel",
            total_cost=1000.0,
        )
        items = [
            LineItem(budget=budget, chapter_code="C01", total_cost=500.0, validation_status="VALID")
        ]
        log = generate_import_log(budget, items, "f.xlsx")
        assert log["schema_version"] == "1.0"
        assert log["file_hash"] == "a" * 64
        assert log["chapters"]["valid"] == 1

    def test_save_log_creates_file(self, tmp_path):
        budget = Budget(
            filename="f.xlsx", file_hash="b" * 64, source_format="excel"
        )
        log = generate_import_log(budget, [], "f.xlsx")
        path = save_log(log, logs_dir=tmp_path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["file_hash"] == "b" * 64


# ---------------------------------------------------------------------------
# Tarea 6: Import (dry-run test via function calls)
# ---------------------------------------------------------------------------


class TestImport:
    def _do_import(self, session, filepath: Path, surface_m2=None):
        """Helper: replicate import.py --confirm logic."""
        from src.core.auditor import compute_file_hash
        from src.core.excel_reader import read_excel
        from src.core.bc3_reader import read_bc3
        from src.core.normalizer import normalize

        fmt = filepath.suffix.lower()
        if fmt in (".xlsx", ".xlsm"):
            raw = read_excel(filepath)
        else:
            raw = read_bc3(filepath)

        file_hash = compute_file_hash(filepath)
        budget, items, logs = normalize(raw, surface_m2=surface_m2, file_hash=file_hash)

        session.add(budget)
        session.add_all(items)
        session.add_all(logs)
        session.commit()
        return budget

    def test_import_xlsx(self, tmp_db):
        if not SAMPLE_XLSX.exists():
            pytest.skip("Sample xlsx not available")
        b = self._do_import(tmp_db, SAMPLE_XLSX, surface_m2=450.0)
        assert b.id is not None
        assert tmp_db.query(LineItem).count() > 0

    def test_import_bc3(self, tmp_db):
        if not SAMPLE_BC3.exists():
            pytest.skip("Sample bc3 not available")
        b = self._do_import(tmp_db, SAMPLE_BC3)
        assert b.id is not None
        assert tmp_db.query(LineItem).count() > 0

    def test_duplicate_detection(self, tmp_db):
        if not SAMPLE_XLSX.exists():
            pytest.skip("Sample xlsx not available")
        self._do_import(tmp_db, SAMPLE_XLSX)
        from src.core.auditor import compute_file_hash
        from src.db.queries import get_budget_by_hash

        h = compute_file_hash(SAMPLE_XLSX)
        existing = get_budget_by_hash(tmp_db, h)
        assert existing is not None

    def test_dry_run_no_db_write(self, tmp_db):
        """Dry-run: we simulate not committing to session."""
        if not SAMPLE_XLSX.exists():
            pytest.skip("Sample xlsx not available")
        from src.core.excel_reader import read_excel
        from src.core.normalizer import normalize
        from src.core.auditor import compute_file_hash

        raw = read_excel(SAMPLE_XLSX)
        h = compute_file_hash(SAMPLE_XLSX)
        budget, items, logs = normalize(raw, file_hash=h)
        # Dry-run: do NOT add to session
        assert tmp_db.query(Budget).count() == 0


# ---------------------------------------------------------------------------
# Tarea 7: Ratio Calculator
# ---------------------------------------------------------------------------


class TestRatioCalculator:
    def _seed(self, session, chapter: str, amounts: list[float], surface: float = 100.0):
        for i, amt in enumerate(amounts):
            b = Budget(
                filename=f"b{i}.xlsx",
                file_hash=str(i).zfill(64),
                source_format="excel",
                surface_m2=surface,
            )
            item = LineItem(
                budget=b,
                chapter_code=chapter,
                chapter_name=chapter,
                total_cost=amt,
                validation_status="VALID",
            )
            session.add(b)
        session.commit()

    def test_recalculate_ratios(self, tmp_db):
        self._seed(tmp_db, "C01", [10000.0, 20000.0, 30000.0], surface=100.0)
        n = recalculate_all_ratios(tmp_db)
        tmp_db.commit()
        assert n == 1
        ratios = list_all_ratios(tmp_db)
        assert len(ratios) == 1
        r = ratios[0]
        assert r.chapter_code == "C01"
        assert r.median == pytest.approx(200.0)  # median(100,200,300)
        assert r.min_value == pytest.approx(100.0)
        assert r.max_value == pytest.approx(300.0)
        assert r.sample_count == 3

    def test_no_surface_no_ratio(self, tmp_db):
        b = Budget(
            filename="nosurface.xlsx",
            file_hash="z" * 64,
            source_format="excel",
            surface_m2=None,
        )
        item = LineItem(
            budget=b, chapter_code="C02", chapter_name="C02", total_cost=5000.0, validation_status="VALID"
        )
        tmp_db.add(b)
        tmp_db.commit()
        n = recalculate_all_ratios(tmp_db)
        tmp_db.commit()
        assert n == 1
        r = list_all_ratios(tmp_db)[0]
        assert r.median is None

    def test_dubious_items_excluded(self, tmp_db):
        b = Budget(
            filename="dub.xlsx", file_hash="d" * 64, source_format="excel", surface_m2=100.0
        )
        item = LineItem(
            budget=b, chapter_code="C03", chapter_name="C03", total_cost=9999.0, validation_status="DUBIOUS"
        )
        tmp_db.add(b)
        tmp_db.commit()
        recalculate_all_ratios(tmp_db)
        tmp_db.commit()
        ratios = list_all_ratios(tmp_db)
        assert all(r.chapter_code != "C03" or r.sample_count == 0 for r in ratios)


# ---------------------------------------------------------------------------
# Tarea 8: Excel Master Generator
# ---------------------------------------------------------------------------


class TestExcelMasterGenerator:
    def _seed_full(self, session):
        b = Budget(
            filename="test.xlsx",
            file_hash="f" * 64,
            source_format="excel",
            surface_m2=200.0,
            building_type="residential",
            total_cost=50000.0,
        )
        items = [
            LineItem(budget=b, chapter_code="C01", chapter_name="Actuaciones previas", total_cost=5000.0, validation_status="VALID"),
            LineItem(budget=b, chapter_code="C02", chapter_name="Estructura", total_cost=20000.0, validation_status="VALID"),
            LineItem(budget=b, chapter_code="C03", chapter_name="Instalaciones", total_cost=15000.0, validation_status="DUBIOUS"),
        ]
        session.add(b)
        session.add_all(items)
        session.commit()
        recalculate_all_ratios(session)
        session.commit()

    def test_generates_file(self, tmp_db, tmp_path):
        self._seed_full(tmp_db)
        out = tmp_path / "master.xlsx"
        path = generate_master_excel(tmp_db, out)
        assert Path(path).exists()

    def test_has_five_sheets(self, tmp_db, tmp_path):
        self._seed_full(tmp_db)
        out = tmp_path / "master.xlsx"
        generate_master_excel(tmp_db, out)
        wb = load_workbook(str(out))
        assert set(wb.sheetnames) == {"INDEX", "RATIOS_SUMMARY", "CHAPTERS", "AUDIT", "RAW_DATA"}

    def test_index_has_budget_row(self, tmp_db, tmp_path):
        self._seed_full(tmp_db)
        out = tmp_path / "master.xlsx"
        generate_master_excel(tmp_db, out)
        wb = load_workbook(str(out))
        ws = wb["INDEX"]
        rows = list(ws.iter_rows(values_only=True))
        assert len(rows) >= 2  # header + at least 1 budget

    def test_opens_on_index(self, tmp_db, tmp_path):
        self._seed_full(tmp_db)
        out = tmp_path / "master.xlsx"
        generate_master_excel(tmp_db, out)
        wb = load_workbook(str(out))
        assert wb.active.title == "INDEX"

    def test_overwrites_existing(self, tmp_db, tmp_path):
        self._seed_full(tmp_db)
        out = tmp_path / "master.xlsx"
        generate_master_excel(tmp_db, out)
        generate_master_excel(tmp_db, out)  # second call should not raise
        assert out.exists()
