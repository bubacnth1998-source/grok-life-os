"""NEXUS — rules-first assistant. Never fakes external LLM."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User
from app.modules.core import dashboard

router = APIRouter(prefix="/nexus", tags=["nexus"])

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@router.get("/status")
def status():
    return {
        "assistant": "NEXUS",
        "mode": "rules",
        "llm_enabled": False,
        "note": "NEXUS usa reglas y datos locales. La integración con un proveedor LLM aún no está implementada; configurar una API key no activa llamadas externas.",
    }

@router.post("/chat")
def chat(body: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    msg = body.message.lower().strip()
    data = dashboard(db, user)
    if any(w in msg for w in ("resumen", "cómo estoy", "como estoy", "dashboard", "estado")):
        reply = f"Pendientes: {data['answers']['pending_count']}. Disponible personal: {data['finance']['personal']['available']} (reservado: {data['finance']['personal']['reserved']}). Proyectos activos: {len(data['projects'])}."
        if data["answers"]["attention"]:
            reply += " Alertas: " + "; ".join(a["message"] for a in data["answers"]["attention"])
        return {"reply": reply, "mode": "rules", "actions_proposed": []}
    if any(w in msg for w in ("tarea", "pendiente", "priorid")):
        items = data["answers"]["priorities"] or data["tasks_open"][:5]
        if not items:
            return {"reply": "No hay tareas abiertas registradas.", "mode": "rules", "actions_proposed": []}
        lines = [f"- {t.get('title')} ({t.get('status', '')})" for t in items]
        return {"reply": "Prioridades actuales:\n" + "\n".join(lines), "mode": "rules", "actions_proposed": []}
    if "objetivo" in msg or "meta" in msg:
        goals = data["memory_goals"]
        if not goals:
            return {"reply": "No hay objetivos confirmados en memoria.", "mode": "rules", "actions_proposed": []}
        return {"reply": "Objetivos:\n" + "\n".join(f"- {g['title']}" for g in goals), "mode": "rules", "actions_proposed": []}
    return {"reply": "Soy NEXUS en modo reglas. Prueba: resumen, tareas, objetivos. No invento datos.", "mode": "rules", "actions_proposed": []}
