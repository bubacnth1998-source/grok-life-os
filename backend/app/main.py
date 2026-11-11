"""Grok LIFE OS — application entry."""
import os
import sys
from pathlib import Path

# Vercel imports this module as backend.app.main. The application uses
# absolute imports rooted at "app", so make the backend package directory
# available before importing any application modules.
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from collections import defaultdict

from app.core.config import settings
from app.db.base import engine, Base
from app.domain import models  # noqa: F401
from app.modules import auth, core, finance, projects, memory, backup, nexus, governance, simulator, audit, time_os, life, automation, habits, business, travel, learning, media, intelligence, privacy

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
os.makedirs(settings.MEDIA_PATH, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/api/docs")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

_buckets: dict[str, list[float]] = defaultdict(list)

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "x"
        now = time.time()
        _buckets[ip] = [t for t in _buckets[ip] if now - t < 60]
        if len(_buckets[ip]) >= 180:
            return JSONResponse({"detail": "Rate limit"}, status_code=429)
        _buckets[ip].append(now)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityMiddleware)

prefix = settings.API_PREFIX
for r in [auth, core, finance, projects, memory, backup, nexus, governance, simulator, audit, time_os, life, automation, habits, business, travel, learning, media, intelligence, privacy]:
    app.include_router(r.router, prefix=prefix)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND)), name="assets")
    @app.get("/")
    def index():
        return FileResponse(FRONTEND / "index.html")
