"""LIFE SIMULATOR — what-if; never mutates real data."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User
from app.domain.finance_service import portfolio_summary
from app.modules.governance import log_event

router = APIRouter(prefix="/simulator", tags=["simulator"])

class SaveScenarioIn(BaseModel):
    monthly_save: Decimal = Field(gt=0)
    months: int = Field(default=12, ge=1, le=360)
    scope: str = "personal"

class TripScenarioIn(BaseModel):
    trip_cost: Decimal = Field(gt=0)
    months_until: int = Field(default=3, ge=0, le=120)
    scope: str = "personal"

def _base(db, user, scope):
    s = portfolio_summary(db, user.id, scope)
    return {"as_of": date.today().isoformat(), "scope": scope, "current_available": s["available"], "current_reserved": s["reserved"], "current_total": s["total"], "mutates_real_data": False}

@router.post("/savings")
def simulate_savings(body: SaveScenarioIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = _base(db, user, body.scope)
    added = float(body.monthly_save) * body.months
    log_event(db, user.id, "nexus", "prepare", "simulate.savings", True)
    return {**base, "scenario": "monthly_savings", "assumptions": [f"Ahorro {float(body.monthly_save)}€/mes x {body.months} meses", "Sin intereses", "No modifica saldos reales"], "projection": {"extra_saved": added, "projected_reserved": base["current_reserved"] + added, "projected_total": base["current_available"] + base["current_reserved"] + added}}

@router.post("/trip")
def simulate_trip(body: TripScenarioIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = _base(db, user, body.scope)
    cost = float(body.trip_cost)
    shortfall = max(0.0, cost - base["current_available"])
    log_event(db, user.id, "nexus", "prepare", "simulate.trip", True)
    return {**base, "scenario": "trip_budget", "assumptions": ["Solo disponible personal", "No crea gasto real"], "projection": {"can_afford_now": base["current_available"] >= cost, "shortfall": shortfall}}

@router.post("/housing")
def simulate_housing(body: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = _base(db, user, body.get("scope", "personal"))
    target = float(body.get("target_price", 0))
    pct = float(body.get("down_payment_pct", 20))
    monthly = float(body.get("monthly_save", 1))
    down = target * pct / 100.0
    need = max(0.0, down - base["current_reserved"])
    months = int(need / monthly) + (1 if need > 0 and monthly > 0 else 0) if monthly > 0 else None
    return {**base, "scenario": "housing_down_payment", "assumptions": ["Solo reservado cuenta como progreso", "Sin hipoteca modelada"], "projection": {"down_payment_needed": down, "gap": need, "months_at_current_savings_rate": months}}

@router.post("/income-change")
def simulate_income(body: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = _base(db, user, body.get("scope", "personal"))
    delta = float(body.get("monthly_income_delta", 0))
    months = int(body.get("months", 12))
    total = delta * months
    return {**base, "scenario": "income_change", "assumptions": ["Sin impuestos modelados", "No altera ledger"], "projection": {"cumulative_delta": total, "projected_available": base["current_available"] + total}}
