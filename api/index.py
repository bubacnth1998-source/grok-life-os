"""Vercel serverless entry — exposes FastAPI app."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/grok_life_os.db")
os.environ.setdefault("LIFE_OS_MEDIA_PATH", "/tmp/grok_life_os_media")

from app.main import app  # noqa: E402

__all__ = ["app"]
