"""LIFE CORE — dashboard from real stored data only."""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Task, Project, Habit, HabitLog, MemoryItem
from app.domain.finance_service import portfolio_summary

router = APIRouter(prefix="/core", tags=["life-core"])

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    open_tasks = db.scalars(select(Task).where(Task.user_id == user.id, Task.status.in_(["todo", "doing"])).order_by(Task.priority.desc())).all()
    projects = db.scalars(select(Project).where(Project.user_id == user.id, Project.status == "active")).all()
    habits = db.scalars(select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True))).all()
    habit_today = []
    for h in habits:
        log = db.scalars(select(HabitLog).where(HabitLog.habit_id == h.id, HabitLog.day == today)).first()
        habit_today.append({"id": h.id, "name": h.name, "completed_today": bool(log and log.completed)})
    goals = db.scalars(select(MemoryItem).where(MemoryItem.user_id == user.id, MemoryItem.kind == "goal", MemoryItem.confidence == "confirmed")).all()
    personal = portfolio_summary(db, user.id, "personal")
    business = portfolio_summary(db, user.id, "business")
    due_today = [t for t in open_tasks if t.due_date == today]
    overdue = [t for t in open_tasks if t.due_date and t.due_date < today]
    alerts = []
    if overdue:
        alerts.append({"level": "warn", "message": f"{len(overdue)} tarea(s) atrasada(s)"})
    if personal["available"] < 0:
        alerts.append({"level": "critical", "message": "Saldo disponible personal negativo"})
    next_actions = []
    for t in overdue[:3] + due_today[:3] + [x for x in open_tasks if x.priority == "high"][:3]:
        if t.id not in {a.get("task_id") for a in next_actions}:
            next_actions.append({"task_id": t.id, "title": t.title, "status": t.status, "due_date": str(t.due_date) if t.due_date else None})
    return {
        "as_of": today.isoformat(),
        "user": {"id": user.id, "full_name": user.full_name},
        "answers": {
            "how_is_life": "Datos reales del sistema; sin indicadores inventados.",
            "pending_count": len(open_tasks),
            "priorities": next_actions[:5],
            "active_goals": [{"id": g.id, "title": g.title} for g in goals],
            "attention": alerts,
            "next": next_actions[:3],
        },
        "finance": {"personal": personal, "business": business},
        "projects": [{"id": p.id, "name": p.name, "progress": p.progress, "status": p.status} for p in projects],
        "tasks_open": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_date": str(t.due_date) if t.due_date else None} for t in open_tasks[:20]],
        "habits_today": habit_today,
        "memory_goals": [{"id": g.id, "title": g.title, "content": g.content} for g in goals],
    }
