"""LIFE GOVERNANCE — action classes, permissions, audit trail."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, GovernanceEvent

router = APIRouter(prefix="/governance", tags=["governance"])

ACTION_CLASSES = {
    "read": {"confirm": False, "description": "Consultar información autorizada"},
    "prepare": {"confirm": False, "description": "Crear propuestas y borradores sin mutar"},
    "reversible": {"confirm": False, "description": "Cambios recuperables"},
    "sensitive": {"confirm": True, "description": "Requiere confirmación explícita"},
    "irreversible": {"confirm": True, "description": "Requiere autorización explícita"},
}
NEXUS_ALLOWED = {"read", "prepare"}

def log_event(db, user_id, actor, action_class, action, allowed, resource=None, detail=None):
    ev = GovernanceEvent(user_id=user_id, actor=actor, action_class=action_class, action=action, resource=resource, allowed=allowed, detail=detail)
    db.add(ev)
    return ev

def assert_agent_allowed(action_class: str, confirmed: bool = False) -> None:
    if action_class in ("read", "prepare"):
        return
    if action_class == "reversible" and confirmed:
        return
    if action_class in ("sensitive", "irreversible") and confirmed:
        return
    raise HTTPException(403, f"Acción '{action_class}' no autorizada sin confirmación explícita del usuario")

@router.get("/policy")
def policy():
    return {"action_classes": ACTION_CLASSES, "nexus_default_allowed": sorted(NEXUS_ALLOWED)}

@router.get("/events")
def list_events(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(GovernanceEvent).where(GovernanceEvent.user_id == user.id).order_by(GovernanceEvent.id.desc()).limit(min(limit, 200))).all()
    return [{"id": e.id, "actor": e.actor, "action_class": e.action_class, "action": e.action, "resource": e.resource, "allowed": e.allowed, "detail": e.detail, "created_at": e.created_at.isoformat() if e.created_at else None} for e in rows]

class AgentActionIn(BaseModel):
    action_class: str
    action: str = Field(min_length=1, max_length=128)
    resource: str | None = None
    confirmed: bool = False
    detail: str | None = None

@router.post("/agent/check")
def agent_check(body: AgentActionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.action_class not in ACTION_CLASSES:
        raise HTTPException(400, "invalid action_class")
    try:
        if body.action_class not in NEXUS_ALLOWED:
            assert_agent_allowed(body.action_class, body.confirmed)
    except HTTPException as e:
        log_event(db, user.id, "nexus", body.action_class, body.action, False, body.resource, body.detail or str(e.detail))
        db.commit()
        raise
    log_event(db, user.id, "nexus", body.action_class, body.action, True, body.resource, body.detail)
    db.commit()
    return {"allowed": True, "action_class": body.action_class, "requires_confirm": ACTION_CLASSES[body.action_class]["confirm"]}
