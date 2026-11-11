"""TRAVEL OS — planning only; never invents bookings."""
from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Trip
from app.modules.governance import log_event
from app.domain.finance_service import portfolio_summary

router = APIRouter(prefix="/travel", tags=["travel"])

class TripIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    status: str = "planning"
    notes: Optional[str] = None

@router.get("/trips")
def list_trips(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Trip).where(Trip.user_id == user.id).order_by(Trip.id.desc())).all()
    return [{"id": t.id, "title": t.title, "destination": t.destination, "budget": float(t.budget) if t.budget is not None else None, "status": t.status} for t in rows]

@router.post("/trips", status_code=201)
def create_trip(body: TripIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.status not in ("planning", "booked", "done", "cancelled"):
        raise HTTPException(400, "invalid status")
    t = Trip(user_id=user.id, title=body.title.strip(), destination=body.destination, start_date=body.start_date, end_date=body.end_date, budget=body.budget, status=body.status, notes=body.notes)
    db.add(t)
    log_event(db, user.id, "user", "reversible", "travel.trip_create", True)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "title": t.title, "disclaimer": "No se confirman reservas externas automáticamente"}

@router.get("/trips/{trip_id}/feasibility")
def trip_feasibility(trip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Trip, trip_id)
    if not t or t.user_id != user.id:
        raise HTTPException(404, "Not found")
    personal = portfolio_summary(db, user.id, "personal")
    budget = float(t.budget or 0)
    return {"trip_id": t.id, "budget": budget, "available": personal["available"], "can_cover_from_available": personal["available"] >= budget if budget else None, "mutates_real_data": False}
