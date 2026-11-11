from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Course
from app.modules.governance import log_event

router = APIRouter(prefix="/learning", tags=["learning"])

class CourseIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None

@router.get("/courses")
def list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Course).where(Course.user_id == user.id)).all()
    return [{"id": c.id, "title": c.title, "progress": c.progress, "status": c.status} for c in rows]

@router.post("/courses", status_code=201)
def create_course(body: CourseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = Course(user_id=user.id, title=body.title.strip(), description=body.description)
    db.add(c)
    log_event(db, user.id, "user", "reversible", "learning.course_create", True)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "title": c.title}

@router.patch("/courses/{course_id}/progress")
def set_progress(course_id: int, progress: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.get(Course, course_id)
    if not c or c.user_id != user.id:
        raise HTTPException(404, "Not found")
    if progress < 0 or progress > 100:
        raise HTTPException(400, "progress 0-100")
    c.progress = progress
    if progress >= 100:
        c.status = "done"
    db.commit()
    return {"id": c.id, "progress": c.progress, "status": c.status}
