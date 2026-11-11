"""LIFE SELF-AUDIT — detect issues; never auto-fix sensitive data."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Account, Posting, Task, MemoryItem, SchemaMeta
from app.domain.finance_service import portfolio_summary
from app.core.config import settings

router = APIRouter(prefix="/audit", tags=["self-audit"])
SCHEMA_VERSION = "0.1.0"

@router.get("/run")
def run_audit(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    findings = []
    meta = db.scalars(select(SchemaMeta).where(SchemaMeta.key == "schema_version")).first()
    if not meta:
        findings.append({"code": "SCHEMA_VERSION_MISSING", "severity": "info", "evidence": "No schema_version", "proposal": "POST /audit/init-schema"})
    mems = db.scalars(select(MemoryItem).where(MemoryItem.user_id == user.id)).all()
    seen = {}
    for m in mems:
        key = (m.kind, m.title.strip().lower())
        if key in seen:
            findings.append({"code": "MEMORY_DUPLICATE", "severity": "warn", "evidence": f"ids {seen[key]} and {m.id}", "proposal": "Fusionar manualmente"})
        else:
            seen[key] = m.id
    personal = portfolio_summary(db, user.id, "personal")
    if personal["available"] < 0:
        findings.append({"code": "FINANCE_NEGATIVE_AVAILABLE", "severity": "critical", "evidence": f"available={personal['available']}", "proposal": "Revisar gastos"})
    if settings.SECRET_KEY.startswith("grok-life-os-dev"):
        findings.append({"code": "DEV_SECRET_KEY", "severity": "warn", "evidence": "default secret", "proposal": "Definir LIFE_OS_SECRET_KEY"})
    modules = {"auth": True, "core": True, "finance": True, "projects": True, "memory": True, "backup": True, "nexus": True, "governance": True, "simulator": True, "self_audit": True, "time": True, "business": True, "automation": True, "habits": True, "life_domains": True, "travel": True, "learning": True, "media": True, "intelligence": True, "connect": False}
    for name, ok in modules.items():
        if not ok:
            findings.append({"code": "MODULE_NOT_IMPLEMENTED", "severity": "info", "evidence": name, "proposal": "Pendiente"})
    summary = {"critical": sum(1 for f in findings if f["severity"] == "critical"), "warn": sum(1 for f in findings if f["severity"] == "warn"), "info": sum(1 for f in findings if f["severity"] == "info")}
    return {"schema_version_expected": SCHEMA_VERSION, "mutates_data": False, "summary": summary, "findings": findings, "modules": modules}

@router.post("/init-schema")
def init_schema(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalars(select(SchemaMeta).where(SchemaMeta.key == "schema_version")).first()
    if row:
        row.value = SCHEMA_VERSION
    else:
        db.add(SchemaMeta(key="schema_version", value=SCHEMA_VERSION))
    db.commit()
    return {"ok": True, "schema_version": SCHEMA_VERSION}
