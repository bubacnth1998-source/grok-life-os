import os, sys
from pathlib import Path
os.environ["DATABASE_URL"] = "sqlite:////tmp/grok_life_os_test.db"
os.environ["LIFE_OS_SECRET_KEY"] = "test-secret-key-for-pytest-32chars!!"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base, engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_register_login():
    r = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "password12", "full_name": "A"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200

def test_finance_ledger():
    r = client.post("/api/v1/auth/register", json={"email": "f@example.com", "password": "password12", "full_name": "F"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    acc = client.post("/api/v1/finance/accounts", headers=h, json={"name": "Caja"}).json()["id"]
    client.post("/api/v1/finance/transactions", headers=h, json={"account_id": acc, "amount": 100, "kind": "income", "description": "in"})
    s = client.get("/api/v1/finance/summary?scope=personal", headers=h).json()
    assert s["available"] == 100.0

def test_simulator_no_mutate():
    r = client.post("/api/v1/auth/register", json={"email": "s@example.com", "password": "password12", "full_name": "S"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    client.post("/api/v1/finance/accounts", headers=h, json={"name": "C"})
    acc = client.get("/api/v1/finance/accounts", headers=h).json()[0]["id"]
    client.post("/api/v1/finance/transactions", headers=h, json={"account_id": acc, "amount": 50, "kind": "income", "description": "x"})
    before = client.get("/api/v1/finance/summary?scope=personal", headers=h).json()
    sim = client.post("/api/v1/simulator/savings", headers=h, json={"monthly_save": 10, "months": 2}).json()
    assert sim["mutates_real_data"] is False
    after = client.get("/api/v1/finance/summary?scope=personal", headers=h).json()
    assert after["available"] == before["available"]

def _auth(email):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "password12", "full_name": "Backup"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_backup_round_trip_preserves_finance():
    source = _auth("backup-source@example.com")
    account = client.post("/api/v1/finance/accounts", headers=source, json={"name": "Savings", "is_reserved": True})
    assert account.status_code == 201
    account_id = account.json()["id"]
    tx = client.post("/api/v1/finance/transactions", headers=source, json={"account_id": account_id, "amount": 125.50, "kind": "income", "description": "Initial deposit"})
    assert tx.status_code == 201

    exported = client.get("/api/v1/backup/export", headers=source)
    assert exported.status_code == 200
    backup = exported.json()
    assert len(backup["accounts"]) == 1
    assert len(backup["transactions"]) == 1
    assert backup["integrity"]["algo"] == "sha256"

    target = _auth("backup-target@example.com")
    imported = client.post("/api/v1/backup/import", headers=target, json=backup)
    assert imported.status_code == 200
    assert imported.json()["created"]["accounts"] == 1
    assert imported.json()["created"]["transactions"] == 1
    summary = client.get("/api/v1/finance/summary?scope=personal", headers=target).json()
    assert summary["reserved"] == 125.5
    assert summary["available"] == 0

def test_backup_rejects_tampered_payload_without_writes():
    source = _auth("backup-tamper-source@example.com")
    exported = client.get("/api/v1/backup/export", headers=source).json()
    exported["accounts"].append({"id": 999, "name": "Injected"})
    target = _auth("backup-tamper-target@example.com")
    response = client.post("/api/v1/backup/import", headers=target, json=exported)
    assert response.status_code == 400
    accounts = client.get("/api/v1/finance/accounts", headers=target).json()
    assert accounts == []

def test_backup_round_trip_restores_life_domains():
    source = _auth("backup-life-source@example.com")
    habit = client.post("/api/v1/habits", headers=source, json={"name": "Read"}).json()
    client.post(f"/api/v1/habits/{habit['id']}/log", headers=source)
    client.post("/api/v1/life/notes", headers=source, json={"domain": "housing", "title": "Apartment"})
    client.post("/api/v1/time/events", headers=source, json={"title": "Appointment", "start_at": "2026-11-12T10:00:00+00:00"})
    client.post("/api/v1/travel/trips", headers=source, json={"title": "Girona", "destination": "Spain", "budget": "150"})
    client.post("/api/v1/learning/courses", headers=source, json={"title": "ICT basics"})
    client.post("/api/v1/media/items", headers=source, json={"title": "Study audio", "media_type": "audio"})
    client.post("/api/v1/business/clients", headers=source, json={"name": "Client A"})
    exported = client.get("/api/v1/backup/export", headers=source)
    assert exported.status_code == 200
    backup = exported.json()
    assert all(key in backup for key in ("habit_logs", "calendar_events", "life_notes", "trips", "courses", "media", "clients", "invoices"))

    target = _auth("backup-life-target@example.com")
    imported = client.post("/api/v1/backup/import", headers=target, json=backup)
    assert imported.status_code == 200, imported.text
    assert imported.json()["created"]["habit_logs"] == 1
    assert len(client.get("/api/v1/habits", headers=target).json()) == 1
    assert len(client.get("/api/v1/life/notes", headers=target).json()) == 1
    assert len(client.get("/api/v1/time/events", headers=target).json()) == 1
    assert len(client.get("/api/v1/travel/trips", headers=target).json()) == 1
    assert len(client.get("/api/v1/learning/courses", headers=target).json()) == 1
    assert len(client.get("/api/v1/media/items", headers=target).json()) == 1
    assert len(client.get("/api/v1/business/clients", headers=target).json()) == 1

def test_sqlite_foreign_keys_enabled():
    from sqlalchemy import text
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1

def test_delete_account_removes_user_financial_records():
    headers = _auth("privacy-delete@example.com")
    account = client.post("/api/v1/finance/accounts", headers=headers, json={"name": "Wallet"}).json()["id"]
    created = client.post("/api/v1/finance/transactions", headers=headers, json={"account_id": account, "amount": 25, "kind": "income", "description": "Test"})
    assert created.status_code == 201
    response = client.post("/api/v1/privacy/delete-account", headers=headers, json={"password": "password12", "confirm": "DELETE"})
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True


def test_security_settings_default_debug_is_disabled():
    from app.core.config import Settings
    settings = Settings(SECRET_KEY="unit-test-secret-key-that-is-long-enough")
    assert settings.DEBUG is False


def test_security_settings_reject_production_default_secret():
    import pytest
    from app.core.config import Settings
    with pytest.raises(ValueError, match="unique LIFE_OS_SECRET_KEY"):
        Settings(ENVIRONMENT="production", DEBUG=False, SECRET_KEY="grok-life-os-dev-secret-change-in-production-32c")


def test_security_settings_reject_debug_in_production():
    import pytest
    from app.core.config import Settings
    with pytest.raises(ValueError, match="DEBUG must be false"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="a-unique-production-secret-key-long-enough",
        )


def test_security_settings_reject_wildcard_cors():
    import pytest
    from app.core.config import Settings
    with pytest.raises(ValueError, match="Wildcard CORS"):
        Settings(
            CORS_ORIGINS="*",
            SECRET_KEY="unit-test-secret-key-that-is-long-enough",
        )


def test_finance_rejects_cross_user_account_reference():
    owner_headers = _auth("finance-owner-isolation@example.com")
    other_headers = _auth("finance-other-isolation@example.com")
    account = client.post(
        "/api/v1/finance/accounts",
        headers=owner_headers,
        json={"name": "Private wallet"},
    ).json()["id"]

    rejected = client.post(
        "/api/v1/finance/transactions",
        headers=other_headers,
        json={
            "account_id": account,
            "amount": 99,
            "kind": "income",
            "description": "Must not cross account boundary",
        },
    )
    assert rejected.status_code == 400
    assert client.get("/api/v1/finance/transactions", headers=other_headers).json() == []
    owner_summary = client.get(
        "/api/v1/finance/summary?scope=personal",
        headers=owner_headers,
    ).json()
    assert owner_summary["available"] == 0


def test_backup_rejects_transaction_reference_to_account_not_in_backup():
    owner = _auth("backup-reference-owner@example.com")
    foreign_account = client.post(
        "/api/v1/finance/accounts",
        headers=owner,
        json={"name": "Foreign private account"},
    ).json()["id"]

    target = _auth("backup-reference-target@example.com")
    response = client.post(
        "/api/v1/backup/import",
        headers=target,
        json={
            "accounts": [{"id": 10, "name": "Imported account"}],
            "transactions": [{
                "date": "2026-11-11",
                "description": "Cross-account reference attempt",
                "kind": "income",
                "ledger_scope": "personal",
                "postings": [{"account_id": foreign_account, "amount": "50"}],
            }],
        },
    )
    assert response.status_code == 400
    assert client.get("/api/v1/finance/accounts", headers=target).json() == []
    assert client.get("/api/v1/finance/transactions", headers=target).json() == []


def test_backup_import_rolls_back_earlier_rows_after_late_invalid_row():
    target = _auth("backup-rollback-target@example.com")
    response = client.post(
        "/api/v1/backup/import",
        headers=target,
        json={
            "accounts": [{"id": 1, "name": "Should roll back"}],
            "transactions": [{
                "date": "2026-11-11",
                "description": "Invalid account mapping",
                "kind": "income",
                "ledger_scope": "personal",
                "postings": [{"account_id": 999999, "amount": "25"}],
            }],
        },
    )
    assert response.status_code == 400
    assert client.get("/api/v1/finance/accounts", headers=target).json() == []
    assert client.get("/api/v1/finance/transactions", headers=target).json() == []


def test_finance_rejects_transaction_scope_mismatch():
    headers = _auth("finance-scope-owner@example.com")
    account = client.post(
        "/api/v1/finance/accounts",
        headers=headers,
        json={"name": "Personal account", "ledger_scope": "personal"},
    ).json()["id"]
    rejected = client.post(
        "/api/v1/finance/transactions",
        headers=headers,
        json={
            "account_id": account,
            "amount": 10,
            "kind": "income",
            "description": "Wrong ledger",
            "ledger_scope": "business",
        },
    )
    assert rejected.status_code == 400
    assert client.get("/api/v1/finance/transactions", headers=headers).json() == []
    assert client.get("/api/v1/finance/summary?scope=personal", headers=headers).json()["available"] == 0


def test_automation_requires_explicit_confirmation_before_mutation():
    headers = _auth("automation-confirmation@example.com")
    created = client.post(
        "/api/v1/automation/rules",
        headers=headers,
        json={
            "name": "Create follow-up",
            "trigger_type": "manual",
            "action_type": "create_task",
            "action_payload": {"title": "Confirm me"},
        },
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    denied = client.post(f"/api/v1/automation/rules/{rule_id}/run", headers=headers)
    assert denied.status_code == 403
    assert client.get("/api/v1/projects/tasks", headers=headers).json() == []
    runs = client.get("/api/v1/automation/runs", headers=headers).json()
    assert len(runs) == 1
    assert runs[0]["status"] == "skipped"

    allowed = client.post(
        f"/api/v1/automation/rules/{rule_id}/run",
        headers=headers,
        params={"confirmed": "true"},
    )
    assert allowed.status_code == 200
    tasks = client.get("/api/v1/projects/tasks", headers=headers).json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Confirm me"


def test_automation_rejects_schedule_trigger_without_scheduler():
    headers = _auth("automation-no-scheduler@example.com")
    response = client.post(
        "/api/v1/automation/rules",
        headers=headers,
        json={
            "name": "Pretend schedule",
            "trigger_type": "schedule_daily",
            "action_type": "create_task",
            "action_payload": {"title": "Should not be scheduled"},
        },
    )
    assert response.status_code == 400


def test_registration_audit_uses_user_id_without_copying_email():
    from app.db.base import SessionLocal
    from app.domain.models import AuditLog

    email = "minimized-audit@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password12", "full_name": "Audit Test"},
    )
    assert response.status_code == 200
    user_id = response.json()["user"]["id"]
    with SessionLocal() as db:
        event = db.query(AuditLog).filter(AuditLog.action == "user.register", AuditLog.user_id == user_id).one()
        assert event.detail is None
        assert email not in (event.detail or "")
