"""Life domains — identity, housing, career, relationships, possessions, obligations."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, LifeDomainNote
from app.modules.governance import log_event

router = APIRouter(prefix="/life", tags=["life-domains"])

DOMAINS = {
    "identity": "Identidad y administración personal",
    "housing": "Vivienda y hogar",
    "career": "Carrera y trabajo",
    "relationships": "Relaciones personales",
    "image": "Imagen, ropa y compras",
    "possessions": "Patrimonio y posesiones",
    "obligations": "Obligaciones y riesgos",
    "knowledge": "Gestión del conocimiento",
}

class DomainNoteIn(BaseModel):
    domain: str
    title: str = Field(min_length=1, max_length=300)
    content: Optional[str] = None
    status: str = "active"

@router.get("/domains")
def list_domains():
    return [{"id": k, "label": v} for k, v in DOMAINS.items()]

@router.get("/notes")
def list_notes(domain: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(LifeDomainNote).where(LifeDomainNote.user_id == user.id)
    if domain:
        if domain not in DOMAINS:
            raise HTTPException(400, "invalid domain")
        q = q.where(LifeDomainNote.domain == domain)
    rows = db.scalars(q.order_by(LifeDomainNote.id.desc())).all()
    return [{"id": n.id, "domain": n.domain, "title": n.title, "content": n.content, "status": n.status} for n in rows]

@router.post("/notes", status_code=201)
def create_note(body: DomainNoteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.domain not in DOMAINS:
        raise HTTPException(400, f"domain must be one of {list(DOMAINS)}")
    n = LifeDomainNote(user_id=user.id, domain=body.domain, title=body.title.strip(), content=body.content, status=body.status)
    db.add(n)
    log_event(db, user.id, "user", "reversible", "life.note_create", True, resource=body.domain)
    db.commit()
    db.refresh(n)
    return {"id": n.id, "domain": n.domain, "title": n.title}

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(LifeDomainNote, note_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(n)
    log_event(db, user.id, "user", "sensitive", "life.note_delete", True, resource=f"note:{note_id}")
    db.commit()
    return {"ok": True}
