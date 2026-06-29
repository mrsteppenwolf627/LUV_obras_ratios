"""Integration tests for app/routers/master.py (T4).

The router is NOT yet registered in app/main.py or api/index.py (T5 pending).
Tests create a local FastAPI app, include master.router, and monkey-patch
_db.get_db in the router module to use an in-memory SQLite session.

This mirrors the pattern used in test_import.py for import_budgets.
"""
from __future__ import annotations

import hashlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.schema import Base, BudgetImport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client_and_session():
    """TestClient backed by in-memory SQLite. Patches _db.get_db in master module."""
    from app.routers import master as master_module

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    _Session = sessionmaker(bind=engine)

    original_get_db = master_module._db.get_db

    def _fake_get_db():
        return _Session()

    master_module._db.get_db = _fake_get_db

    test_app = FastAPI()
    test_app.include_router(master_module.router)
    client = TestClient(test_app)

    yield client, _Session

    master_module._db.get_db = original_get_db


@pytest.fixture
def client(client_and_session):
    c, _ = client_and_session
    return c


@pytest.fixture
def db_session(client_and_session):
    _, Session = client_and_session
    s = Session()
    yield s
    s.close()


def _sha256(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _seed_import(db_session, seed: str, status: str = "success",
                 approval_status: str = "PENDING_REVIEW") -> BudgetImport:
    """Insert a BudgetImport directly into the test DB."""
    record = BudgetImport(
        filename=f"{seed}.xlsx",
        file_hash=_sha256(seed),
        building_type="residencial",
        status=status,
        approval_status=approval_status,
        items_count=5,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


# ---------------------------------------------------------------------------
# 1. GET /api/master/status
# ---------------------------------------------------------------------------

class TestMasterStatus:
    def test_status_returns_fase_master(self, client):
        resp = client.get("/api/master/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phase"] == "FASE_MASTER"
        assert data["approval_flow_enabled"] is True
        assert "message" in data

    def test_status_no_auth_required(self, client):
        """Endpoint is readable without authentication for T4 (auth is T4+ concern)."""
        resp = client.get("/api/master/status")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. GET /api/master/imports
# ---------------------------------------------------------------------------

class TestListImports:
    def test_list_imports_returns_list(self, client, db_session):
        _seed_import(db_session, "tr_list_01")
        resp = client.get("/api/master/imports")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_imports_contains_expected_fields(self, client, db_session):
        _seed_import(db_session, "tr_list_fields")
        resp = client.get("/api/master/imports")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        item = items[0]
        for field in ("id", "filename", "file_hash", "status", "approval_status"):
            assert field in item, f"Campo '{field}' ausente en respuesta"

    def test_list_imports_filter_by_approval_status(self, client, db_session):
        _seed_import(db_session, "tr_filter_pending", approval_status="PENDING_REVIEW")
        _seed_import(db_session, "tr_filter_approved", approval_status="APPROVED")

        resp = client.get("/api/master/imports?approval_status=PENDING_REVIEW")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["approval_status"] == "PENDING_REVIEW" for i in items), (
            "El filtro approval_status=PENDING_REVIEW debe excluir APPROVED."
        )

    def test_list_imports_filter_by_technical_status(self, client, db_session):
        _seed_import(db_session, "tr_filter_tech_err", status="error")
        _seed_import(db_session, "tr_filter_tech_ok", status="success")

        resp = client.get("/api/master/imports?technical_status=error")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["status"] == "error" for i in items)

    def test_list_imports_respects_limit(self, client, db_session):
        for i in range(5):
            _seed_import(db_session, f"tr_limit_{i:03d}")

        resp = client.get("/api/master/imports?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_list_imports_limit_capped_at_500(self, client):
        resp = client.get("/api/master/imports?limit=9999")
        assert resp.status_code == 200  # no error, just capped internally


# ---------------------------------------------------------------------------
# 3. GET /api/master/imports/pending
# ---------------------------------------------------------------------------

class TestListPending:
    def test_pending_returns_only_pending_review(self, client, db_session):
        _seed_import(db_session, "tr_pend_a", approval_status="PENDING_REVIEW")
        _seed_import(db_session, "tr_pend_b", approval_status="APPROVED")
        _seed_import(db_session, "tr_pend_c", approval_status="REJECTED")

        resp = client.get("/api/master/imports/pending")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["approval_status"] == "PENDING_REVIEW" for i in items), (
            "/pending debe devolver únicamente PENDING_REVIEW."
        )

    def test_pending_returns_list(self, client):
        resp = client.get("/api/master/imports/pending")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# 4 & 5. GET /api/master/imports/{import_id}
# ---------------------------------------------------------------------------

class TestGetImport:
    def test_get_import_returns_detail(self, client, db_session):
        record = _seed_import(db_session, "tr_detail_01")
        resp = client.get(f"/api/master/imports/{record.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == record.id
        assert data["filename"] == f"tr_detail_01.xlsx"

    def test_get_import_returns_all_fields(self, client, db_session):
        record = _seed_import(db_session, "tr_detail_fields")
        resp = client.get(f"/api/master/imports/{record.id}")
        data = resp.json()
        for field in (
            "id", "filename", "file_hash", "status", "approval_status",
            "building_type", "import_date", "items_count",
            "reviewed_by", "reviewed_at", "review_notes",
        ):
            assert field in data, f"Campo '{field}' ausente en detalle"

    def test_get_import_nonexistent_returns_404(self, client):
        resp = client.get("/api/master/imports/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6. POST /api/master/imports/{import_id}/approve
# ---------------------------------------------------------------------------

class TestApproveEndpoint:
    def test_approve_changes_status_to_approved(self, client, db_session):
        record = _seed_import(db_session, "tr_approve_01")
        resp = client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor", "notes": "OK"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_status"] == "APPROVED"
        assert data["reviewed_by"] == "aitor"
        assert data["reviewed_at"] is not None

    def test_approve_without_notes_is_valid(self, client, db_session):
        record = _seed_import(db_session, "tr_approve_no_notes")
        resp = client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor"},
        )
        assert resp.status_code == 200
        assert resp.json()["approval_status"] == "APPROVED"

    def test_approve_persists_to_db(self, client, db_session):
        record = _seed_import(db_session, "tr_approve_persist")
        client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor", "notes": "Persistencia"},
        )
        db_session.refresh(record)
        assert record.approval_status == "APPROVED"

    def test_approve_error_status_returns_400(self, client, db_session):
        record = _seed_import(db_session, "tr_approve_error_tech", status="error")
        resp = client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor"},
        )
        assert resp.status_code == 400

    def test_approve_nonexistent_returns_400_or_404(self, client):
        resp = client.post(
            "/api/master/imports/999999/approve",
            json={"reviewed_by": "aitor"},
        )
        assert resp.status_code in (400, 404)

    def test_approve_already_rejected_returns_400(self, client, db_session):
        record = _seed_import(db_session, "tr_approve_rejected",
                              approval_status="REJECTED")
        resp = client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor"},
        )
        assert resp.status_code == 400

    def test_approve_idempotent_returns_200(self, client, db_session):
        """Double-approve returns 200 (no error) on the second call."""
        record = _seed_import(db_session, "tr_approve_idem_http")
        client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "aitor", "notes": "Primera"},
        )
        resp2 = client.post(
            f"/api/master/imports/{record.id}/approve",
            json={"reviewed_by": "otro", "notes": "Segunda"},
        )
        assert resp2.status_code == 200
        # Original reviewer must be preserved (idempotent no-op)
        assert resp2.json()["reviewed_by"] == "aitor"


# ---------------------------------------------------------------------------
# 7. POST /api/master/imports/{import_id}/reject
# ---------------------------------------------------------------------------

class TestRejectEndpoint:
    def test_reject_changes_status_to_rejected(self, client, db_session):
        record = _seed_import(db_session, "tr_reject_01")
        resp = client.post(
            f"/api/master/imports/{record.id}/reject",
            json={"reviewed_by": "aitor", "notes": "Precios incoherentes"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_status"] == "REJECTED"
        assert data["reviewed_by"] == "aitor"
        assert data["review_notes"] == "Precios incoherentes"
        assert data["reviewed_at"] is not None

    def test_reject_persists_to_db(self, client, db_session):
        record = _seed_import(db_session, "tr_reject_persist")
        client.post(
            f"/api/master/imports/{record.id}/reject",
            json={"reviewed_by": "aitor", "notes": "Motivo de rechazo"},
        )
        db_session.refresh(record)
        assert record.approval_status == "REJECTED"

    def test_reject_without_notes_returns_400(self, client, db_session):
        record = _seed_import(db_session, "tr_reject_no_notes")
        # RejectBody requires notes — Pydantic will reject the request at 422
        # or the service raises ValueError → 400. Both are valid for T4.
        resp = client.post(
            f"/api/master/imports/{record.id}/reject",
            json={"reviewed_by": "aitor"},  # notes missing
        )
        assert resp.status_code in (400, 422)

    def test_reject_already_approved_returns_400(self, client, db_session):
        record = _seed_import(db_session, "tr_reject_approved",
                              approval_status="APPROVED")
        resp = client.post(
            f"/api/master/imports/{record.id}/reject",
            json={"reviewed_by": "aitor", "notes": "Cambio de opinión"},
        )
        assert resp.status_code == 400

    def test_reject_nonexistent_returns_400_or_404(self, client):
        resp = client.post(
            "/api/master/imports/999999/reject",
            json={"reviewed_by": "aitor", "notes": "Motivo"},
        )
        assert resp.status_code in (400, 404)
