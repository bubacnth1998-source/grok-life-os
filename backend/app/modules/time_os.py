"""TIME OS — agenda local."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, CalendarEvent, Task
from app.modules.governance import log_event

router = APIRouter(prefix="/time", tags=["time"])

class EventIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = None

@router.get("/events")
def list_events(from_dt: Optional[datetime] = None, to_dt: Optional[datetime] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(CalendarEvent).where(CalendarEvent.user_id == user.id)
    if from_dt:
        q = q.where(CalendarEvent.start_at >= from_dt)
    if to_dt:
        q = q.where(CalendarEvent.start_at <= to_dt)
    rows = db.scalars(q.order_by(CalendarEvent.start_at)).all()
    return [{"id": e.id, "title": e.title, "start_at": e.start_at.isoformat() if e.start_at else None, "end_at": e.end_at.isoformat() if e.end_at else None, "all_day": e.all_day} for e in rows]

@router.post("/events", status_code=201)
def create_event(body: EventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.end_at and body.end_at < body.start_at:
        raise HTTPException(400, "end_at must be >= start_at")
    conflicts = []
    if not body.all_day:
        end = body.end_at or (body.start_at + timedelta(hours=1))
        for e in db.scalars(select(CalendarEvent).where(CalendarEvent.user_id == user.id)).all():
            e_end = e.end_at or (e.start_at + timedelta(hours=1))
            if body.start_at < e_end and end > e.start_at:
                conflicts.append({"id": e.id, "title": e.title})
    ev = CalendarEvent(user_id=user.id, title=body.title.strip(), description=body.description, start_at=body.start_at, end_at=body.end_at, all_day=body.all_day, location=body.location)
    db.add(ev)
    log_event(db, user.id, "user", "reversible", "time.event_create", True)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id, "title": ev.title, "conflicts": conflicts}

@router.get("/agenda/today")
def agenda_today(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    events = db.scalars(select(CalendarEvent).where(CalendarEvent.user_id == user.id, CalendarEvent.start_at >= start, CalendarEvent.start_at < end).order_by(CalendarEvent.start_at)).all()
    tasks = db.scalars(select(Task).where(Task.user_id == user.id, Task.status.in_(["todo", "doing"]), Task.due_date == start.date())).all()
    return {"date": start.date().isoformat(), "events": [{"id": e.id, "title": e.title, "start_at": e.start_at.isoformat()} for e in events], "tasks_due": [{"id": t.id, "title": t.title} for t in tasks]}

@router.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    e = db.get(CalendarEvent, event_id)
    if not e or e.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(e)
    db.commit()
    return {"ok": True}
