"""Export / import — backup & recovery."""
import hashlib
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, MemoryItem, Project, Task, Habit, Account

router = APIRouter(prefix="/backup", tags=["backup"])

@router.get("/export")
def export_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "app": "grok-life-os",
        "version": "0.1.0",
        "user": {"email": user.email, "full_name": user.full_name},
        "memory": [{"kind": m.kind, "title": m.title, "content": m.content, "confidence": m.confidence, "tags": m.tags} for m in db.scalars(select(MemoryItem).where(MemoryItem.user_id == user.id)).all()],
        "projects": [{"name": p.name, "description": p.description, "status": p.status, "progress": p.progress, "priority": p.priority} for p in db.scalars(select(Project).where(Project.user_id == user.id)).all()],
        "tasks": [{"title": t.title, "status": t.status, "priority": t.priority} for t in db.scalars(select(Task).where(Task.user_id == user.id)).all()],
        "habits": [{"name": h.name, "frequency": h.frequency} for h in db.scalars(select(Habit).where(Habit.user_id == user.id)).all()],
        "accounts": [{"name": a.name, "currency": a.currency, "ledger_scope": a.ledger_scope, "is_reserved": a.is_reserved} for a in db.scalars(select(Account).where(Account.user_id == user.id)).all()],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["integrity"] = {"algo": "sha256", "hex": hashlib.sha256(raw.encode()).hexdigest()}
    return payload

class ImportIn(BaseModel):
    memory: list[dict] = []
    projects: list[dict] = []
    tasks: list[dict] = []
    habits: list[dict] = []

@router.post("/import")
def import_data(body: ImportIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    created = {"memory": 0, "projects": 0, "tasks": 0, "habits": 0}
    for m in body.memory:
        db.add(MemoryItem(user_id=user.id, kind=m.get("kind", "fact"), title=str(m.get("title", "imported"))[:300], content=m.get("content"), confidence=m.get("confidence", "confirmed"), source="import", tags=m.get("tags")))
        created["memory"] += 1
    for p in body.projects:
        db.add(Project(user_id=user.id, name=str(p.get("name", "imported"))[:200], description=p.get("description"), status=p.get("status", "active"), progress=int(p.get("progress") or 0), priority=p.get("priority", "medium")))
        created["projects"] += 1
    for t in body.tasks:
        db.add(Task(user_id=user.id, title=str(t.get("title", "imported"))[:300], status=t.get("status", "todo"), priority=t.get("priority", "medium")))
        created["tasks"] += 1
    for h in body.habits:
        db.add(Habit(user_id=user.id, name=str(h.get("name", "imported"))[:150], frequency=h.get("frequency", "daily")))
        created["habits"] += 1
    db.commit()
    return {"ok": True, "created": created}
