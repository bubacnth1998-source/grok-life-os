"""Habits — wellness light (non-diagnostic)."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Habit, HabitLog
from app.modules.governance import log_event

router = APIRouter(prefix="/habits", tags=["habits"])


class HabitIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    frequency: str = "daily"


@router.get("")
def list_habits(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True))).all()
    today = date.today()
    out = []
    for h in rows:
        log = db.scalars(select(HabitLog).where(HabitLog.habit_id == h.id, HabitLog.day == today)).first()
        out.append({"id": h.id, "name": h.name, "frequency": h.frequency, "completed_today": bool(log and log.completed)})
    return out


@router.post("", status_code=201)
def create_habit(body: HabitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    h = Habit(user_id=user.id, name=body.name.strip(), frequency=body.frequency)
    db.add(h)
    log_event(db, user.id, "user", "reversible", "habit.create", True)
    db.commit()
    db.refresh(h)
    return {"id": h.id, "name": h.name}


@router.post("/{habit_id}/log")
def log_habit(habit_id: int, day: Optional[date] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    h = db.get(Habit, habit_id)
    if not h or h.user_id != user.id:
        raise HTTPException(404, "Not found")
    d = day or date.today()
    existing = db.scalars(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.day == d)).first()
    if existing:
        existing.completed = True
    else:
        db.add(HabitLog(habit_id=habit_id, day=d, completed=True))
    log_event(db, user.id, "user", "reversible", "habit.log", True, resource=f"habit:{habit_id}")
    db.commit()
    return {"ok": True, "day": d.isoformat()}
