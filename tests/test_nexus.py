"""NEXUS — rules-only assistant; never invents facts outside stored data."""
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
        json={"email": email, "password": "password12", "full_name": "Nexus"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_nexus_status_is_rules_only():
    st = client.get("/api/v1/nexus/status").json()
    assert st["mode"] == "rules"
    assert st["llm_enabled"] is False


def test_nexus_summary_reflects_real_counts():
    h = _headers("nexus-summary@example.com")
    client.post("/api/v1/projects/tasks", headers=h, json={"title": "Alpha"})
    client.post("/api/v1/projects/tasks", headers=h, json={"title": "Beta"})
    client.post(
        "/api/v1/memory",
        headers=h,
        json={"kind": "goal", "title": "Run daily", "confidence": "confirmed"},
    )
    chat = client.post(
        "/api/v1/nexus/chat",
        headers=h,
        json={"message": "dame un resumen"},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["mode"] == "rules"
    assert "Pendientes: 2" in body["reply"]
    goals = client.post(
        "/api/v1/nexus/chat",
        headers=h,
        json={"message": "cuáles son mis objetivos"},
    ).json()
    assert "Run daily" in goals["reply"]


def test_nexus_unknown_prompt_does_not_fabricate():
    h = _headers("nexus-unknown@example.com")
    r = client.post(
        "/api/v1/nexus/chat",
        headers=h,
        json={"message": "predice mi futuro financiero exacto"},
    )
    assert r.status_code == 200
    reply = r.json()["reply"].lower()
    assert "no invento" in reply or "modo reglas" in reply
