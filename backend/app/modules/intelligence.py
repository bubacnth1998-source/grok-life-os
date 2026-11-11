"""INTELLIGENCE OS — facts vs hypotheses from real data only."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Task, Project, LedgerTransaction
from app.domain.finance_service import portfolio_summary
from datetime import date, timedelta

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/snapshot")
def snapshot(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    personal = portfolio_summary(db, user.id, "personal")
    open_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.user_id == user.id, Task.status.in_(["todo", "doing"]))) or 0
    projects_active = db.scalar(select(func.count()).select_from(Project).where(Project.user_id == user.id, Project.status == "active")) or 0
    facts = [
        {"type": "fact", "text": f"Tareas abiertas: {open_tasks}"},
        {"type": "fact", "text": f"Proyectos activos: {projects_active}"},
        {"type": "fact", "text": f"Disponible personal: {personal['available']}"},
    ]
    hypotheses = []
    if open_tasks > 10:
        hypotheses.append({"type": "hypothesis", "text": "Carga de tareas alta", "basis": "open_tasks > 10"})
    return {"facts": facts, "hypotheses": hypotheses, "disclaimer": "Las hipótesis no son certezas."}
