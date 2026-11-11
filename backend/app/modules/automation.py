"""AUTOMATION OS — rules with governance gates."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, AutomationRule, AutomationRun, Task, MemoryItem
from app.modules.governance import log_event, assert_agent_allowed

router = APIRouter(prefix="/automation", tags=["automation"])

class RuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    trigger_type: str = "manual"
    action_type: str
    action_payload: dict = Field(default_factory=dict)

@router.get("/rules")
def list_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(AutomationRule).where(AutomationRule.user_id == user.id)).all()
    return [{"id": r.id, "name": r.name, "trigger_type": r.trigger_type, "action_type": r.action_type, "action_payload": json.loads(r.action_payload or "{}"), "is_active": r.is_active} for r in rows]

@router.post("/rules", status_code=201)
def create_rule(body: RuleIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.trigger_type != "manual":
        raise HTTPException(400, "Only manual triggers are supported; scheduling requires a configured scheduler")
    if body.action_type not in ("create_task", "memory_note"):
        raise HTTPException(400, "invalid action_type")
    r = AutomationRule(user_id=user.id, name=body.name.strip(), trigger_type=body.trigger_type, action_type=body.action_type, action_payload=json.dumps(body.action_payload, ensure_ascii=False))
    db.add(r)
    log_event(db, user.id, "user", "reversible", "automation.rule_create", True)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "name": r.name}

@router.post("/rules/{rule_id}/run")
def run_rule(rule_id: int, confirmed: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(AutomationRule, rule_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Rule not found")
    if not r.is_active:
        raise HTTPException(400, "Rule inactive")
    try:
        assert_agent_allowed("reversible", confirmed=confirmed)
    except HTTPException:
        db.add(AutomationRun(rule_id=r.id, user_id=user.id, status="skipped", detail="not confirmed"))
        db.commit()
        raise
    payload = json.loads(r.action_payload or "{}")
    detail = ""
    if r.action_type == "create_task":
        title = str(payload.get("title") or r.name)[:300]
        db.add(Task(user_id=user.id, title=title, priority=payload.get("priority", "medium")))
        detail = f"task:{title}"
    elif r.action_type == "memory_note":
        m = MemoryItem(user_id=user.id, kind=payload.get("kind", "fact"), title=str(payload.get("title") or r.name)[:300], content=payload.get("content"), confidence="confirmed", source="automation")
        db.add(m)
        detail = "memory"
    r.last_run_at = datetime.now(timezone.utc)
    db.add(AutomationRun(rule_id=r.id, user_id=user.id, status="ok", detail=detail))
    log_event(db, user.id, "automation", "reversible", "automation.run", True, detail=detail)
    db.commit()
    return {"ok": True, "detail": detail}

@router.get("/runs")
def list_runs(limit: int = 30, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(AutomationRun).where(AutomationRun.user_id == user.id).order_by(AutomationRun.id.desc()).limit(min(limit, 100))).all()
    return [{"id": x.id, "rule_id": x.rule_id, "status": x.status, "detail": x.detail} for x in rows]

@router.post("/rules/{rule_id}/disable")
def disable_rule(rule_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(AutomationRule, rule_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Not found")
    r.is_active = False
    db.commit()
    return {"ok": True, "is_active": False}
