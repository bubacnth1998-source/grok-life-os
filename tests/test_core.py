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
