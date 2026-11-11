from datetime import date as date_cls
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Project, Task

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: str = "medium"
    target_date: Optional[date_cls] = None

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    project_id: int | None = None
    priority: str = "medium"
    due_date: Optional[date_cls] = None

@router.get("")
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Project).where(Project.user_id == user.id)).all()
    return [{"id": p.id, "name": p.name, "status": p.status, "progress": p.progress, "priority": p.priority} for p in rows]

@router.post("", status_code=201)
def create_project(body: ProjectIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = Project(user_id=user.id, name=body.name.strip(), description=body.description, priority=body.priority, target_date=body.target_date)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}

@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Task).where(Task.user_id == user.id).order_by(Task.id.desc())).all()
    return [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "project_id": t.project_id, "due_date": str(t.due_date) if t.due_date else None} for t in rows]

@router.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.project_id:
        p = db.get(Project, body.project_id)
        if not p or p.user_id != user.id:
            raise HTTPException(404, "Project not found")
    t = Task(user_id=user.id, title=body.title.strip(), project_id=body.project_id, priority=body.priority, due_date=body.due_date)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "title": t.title}

@router.patch("/tasks/{task_id}")
def update_task(task_id: int, status: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Task, task_id)
    if not t or t.user_id != user.id:
        raise HTTPException(404, "Task not found")
    if status not in ("todo", "doing", "done", "cancelled"):
        raise HTTPException(400, "invalid status")
    t.status = status
    db.commit()
    return {"id": t.id, "status": t.status}
