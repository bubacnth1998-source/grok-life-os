from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, MediaItem
from app.modules.governance import log_event

router = APIRouter(prefix="/media", tags=["media"])

class MediaIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    media_type: str = "other"
    url_or_path: Optional[str] = None
    tags: Optional[str] = None

@router.get("/items")
def list_media(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(MediaItem).where(MediaItem.user_id == user.id).order_by(MediaItem.id.desc())).all()
    return [{"id": m.id, "title": m.title, "media_type": m.media_type, "url_or_path": m.url_or_path, "tags": m.tags} for m in rows]

@router.post("/items", status_code=201)
def create_media(body: MediaIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.media_type not in ("video", "audio", "image", "document", "other"):
        raise HTTPException(400, "invalid media_type")
    m = MediaItem(user_id=user.id, title=body.title.strip(), media_type=body.media_type, url_or_path=body.url_or_path, tags=body.tags)
    db.add(m)
    log_event(db, user.id, "user", "reversible", "media.create", True)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title}
