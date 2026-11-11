"""Auth abuse controls — failed login throttling."""
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/grok_life_os_test.db")
os.environ.setdefault("LIFE_OS_SECRET_KEY", "test-secret-key-for-pytest-32chars!!")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.modules import auth as auth_mod

client = TestClient(app)


def test_login_throttles_after_repeated_failures():
    email = "throttle-user@example.com"
    # Isolate from other tests' in-memory counters
    auth_mod._failed_logins.clear()

    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password12", "full_name": "T"},
    )
    assert reg.status_code == 200

    for _ in range(8):
        bad = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert bad.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert blocked.status_code == 429

    # Correct password also blocked while window is active
    still = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password12"},
    )
    assert still.status_code == 429
