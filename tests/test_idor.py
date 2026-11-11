"""Negative isolation tests — user A must not mutate or read user B resources by id."""
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/grok_life_os_test.db")
os.environ.setdefault("LIFE_OS_SECRET_KEY", "test-secret-key-for-pytest-32chars!!")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _headers(email: str) -> dict:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password12", "full_name": "Iso"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_idor_task_update_rejects_foreign_task():
    owner = _headers("idor-task-owner@example.com")
    other = _headers("idor-task-other@example.com")
    task = client.post(
        "/api/v1/projects/tasks",
        headers=owner,
        json={"title": "Owner only"},
    ).json()
    rejected = client.patch(
        f"/api/v1/projects/tasks/{task['id']}",
        headers=other,
        params={"status": "done"},
    )
    assert rejected.status_code == 404
    still = client.get("/api/v1/projects/tasks", headers=owner).json()
    assert still[0]["status"] == "todo"


def test_idor_task_cannot_attach_foreign_project():
    owner = _headers("idor-proj-owner@example.com")
    other = _headers("idor-proj-other@example.com")
    project = client.post(
        "/api/v1/projects",
        headers=owner,
        json={"name": "Secret"},
    ).json()
    rejected = client.post(
        "/api/v1/projects/tasks",
        headers=other,
        json={"title": "Hijack", "project_id": project["id"]},
    )
    assert rejected.status_code == 404
    assert client.get("/api/v1/projects/tasks", headers=other).json() == []


def test_idor_memory_update_and_delete_reject_foreign():
    owner = _headers("idor-mem-owner@example.com")
    other = _headers("idor-mem-other@example.com")
    item = client.post(
        "/api/v1/memory",
        headers=owner,
        json={"kind": "fact", "title": "Private fact", "confidence": "confirmed"},
    ).json()
    assert client.patch(
        f"/api/v1/memory/{item['id']}",
        headers=other,
        json={"title": "Stolen"},
    ).status_code == 404
    assert client.get(f"/api/v1/memory/{item['id']}/history", headers=other).status_code == 404
    assert client.delete(f"/api/v1/memory/{item['id']}", headers=other).status_code == 404
    remaining = client.get("/api/v1/memory", headers=owner).json()
    assert any(m["id"] == item["id"] and m["title"] == "Private fact" for m in remaining)


def test_idor_habit_log_rejects_foreign_habit():
    owner = _headers("idor-habit-owner@example.com")
    other = _headers("idor-habit-other@example.com")
    habit = client.post(
        "/api/v1/habits",
        headers=owner,
        json={"name": "Owner habit"},
    ).json()
    rejected = client.post(f"/api/v1/habits/{habit['id']}/log", headers=other)
    assert rejected.status_code == 404
    listed = client.get("/api/v1/habits", headers=owner).json()
    assert listed[0]["completed_today"] is False


def test_idor_life_note_delete_rejects_foreign():
    owner = _headers("idor-life-owner@example.com")
    other = _headers("idor-life-other@example.com")
    note = client.post(
        "/api/v1/life/notes",
        headers=owner,
        json={"domain": "housing", "title": "My lease"},
    ).json()
    assert client.delete(f"/api/v1/life/notes/{note['id']}", headers=other).status_code == 404
    assert len(client.get("/api/v1/life/notes", headers=owner).json()) == 1


def test_idor_calendar_delete_rejects_foreign():
    owner = _headers("idor-time-owner@example.com")
    other = _headers("idor-time-other@example.com")
    event = client.post(
        "/api/v1/time/events",
        headers=owner,
        json={"title": "Private", "start_at": "2026-12-01T10:00:00+00:00"},
    ).json()
    assert client.delete(f"/api/v1/time/events/{event['id']}", headers=other).status_code == 404
    assert len(client.get("/api/v1/time/events", headers=owner).json()) == 1


def test_idor_trip_feasibility_rejects_foreign():
    owner = _headers("idor-trip-owner@example.com")
    other = _headers("idor-trip-other@example.com")
    trip = client.post(
        "/api/v1/travel/trips",
        headers=owner,
        json={"title": "Private trip", "budget": "200"},
    ).json()
    assert client.get(
        f"/api/v1/travel/trips/{trip['id']}/feasibility",
        headers=other,
    ).status_code == 404


def test_idor_invoice_update_rejects_foreign():
    owner = _headers("idor-inv-owner@example.com")
    other = _headers("idor-inv-other@example.com")
    inv = client.post(
        "/api/v1/business/invoices",
        headers=owner,
        json={"number": "INV-1", "amount": "100"},
    ).json()
    rejected = client.patch(
        f"/api/v1/business/invoices/{inv['id']}",
        headers=other,
        params={"status": "paid"},
    )
    assert rejected.status_code == 404
    listed = client.get("/api/v1/business/invoices", headers=owner).json()
    assert listed[0]["status"] == "draft"


def test_idor_automation_run_rejects_foreign_rule():
    owner = _headers("idor-auto-owner@example.com")
    other = _headers("idor-auto-other@example.com")
    rule = client.post(
        "/api/v1/automation/rules",
        headers=owner,
        json={
            "name": "Owner rule",
            "trigger_type": "manual",
            "action_type": "create_task",
            "action_payload": {"title": "Owned"},
        },
    ).json()
    assert client.post(
        f"/api/v1/automation/rules/{rule['id']}/run",
        headers=other,
        params={"confirmed": "true"},
    ).status_code == 404
    assert client.get("/api/v1/projects/tasks", headers=other).json() == []
