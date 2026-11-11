"""LIFE MEMORY — long-term memory with provenance and revision history."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, MemoryItem, MemoryRevision
from app.modules.governance import log_event

router = APIRouter(prefix="/memory", tags=["memory"])

class MemoryIn(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=300)
    content: str | None = None
    confidence: str = "confirmed"
    tags: str | None = None

class MemoryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    confidence: str | None = None
    tags: str | None = None

def _rev(db, m, user_id, change_type):
    db.add(MemoryRevision(memory_id=m.id, user_id=user_id, snapshot_title=m.title, snapshot_content=m.content, snapshot_confidence=m.confidence, change_type=change_type))

@router.get("")
def list_memory(kind: str | None = None, q: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(MemoryItem).where(MemoryItem.user_id == user.id)
    if kind:
        query = query.where(MemoryItem.kind == kind)
    if q:
        like = f"%{q}%"
        query = query.where(or_(MemoryItem.title.ilike(like), MemoryItem.content.ilike(like)))
    rows = db.scalars(query.order_by(MemoryItem.id.desc())).all()
    return [{"id": m.id, "kind": m.kind, "title": m.title, "content": m.content, "confidence": m.confidence, "source": m.source, "tags": m.tags} for m in rows]

@router.post("", status_code=201)
def create_memory(body: MemoryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.kind not in ("preference", "goal", "fact", "decision", "pending"):
        raise HTTPException(400, "invalid kind")
    if body.confidence not in ("confirmed", "inferred", "pending"):
        raise HTTPException(400, "invalid confidence")
    title = body.title.strip()
    dup = db.scalars(select(MemoryItem).where(MemoryItem.user_id == user.id, MemoryItem.kind == body.kind, MemoryItem.title == title)).first()
    m = MemoryItem(user_id=user.id, kind=body.kind, title=title, content=body.content, confidence=body.confidence, source="user", tags=body.tags)
    db.add(m)
    db.flush()
    _rev(db, m, user.id, "create")
    log_event(db, user.id, "user", "reversible", "memory.create", True, resource=f"memory:{m.id}")
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title, "duplicate_of": dup.id if dup else None}

@router.patch("/{item_id}")
def update_memory(item_id: int, body: MemoryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.get(MemoryItem, item_id)
    if not m or m.user_id != user.id:
        raise HTTPException(404, "Not found")
    _rev(db, m, user.id, "update")
    if body.title is not None:
        m.title = body.title.strip()
    if body.content is not None:
        m.content = body.content
    if body.confidence is not None:
        if body.confidence not in ("confirmed", "inferred", "pending"):
            raise HTTPException(400, "invalid confidence")
        m.confidence = body.confidence
    if body.tags is not None:
        m.tags = body.tags
    m.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": m.id, "title": m.title, "confidence": m.confidence}

@router.get("/{item_id}/history")
def memory_history(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.get(MemoryItem, item_id)
    if not m or m.user_id != user.id:
        raise HTTPException(404, "Not found")
    rows = db.scalars(select(MemoryRevision).where(MemoryRevision.memory_id == item_id).order_by(MemoryRevision.id.desc())).all()
    return [{"id": r.id, "change_type": r.change_type, "title": r.snapshot_title, "content": r.snapshot_content, "confidence": r.snapshot_confidence} for r in rows]

@router.delete("/{item_id}")
def delete_memory(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.get(MemoryItem, item_id)
    if not m or m.user_id != user.id:
        raise HTTPException(404, "Not found")
    _rev(db, m, user.id, "delete")
    db.delete(m)
    db.commit()
    return {"ok": True}
