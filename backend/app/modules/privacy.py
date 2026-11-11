"""Privacy / GDPR-oriented endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User
from app.core.security import verify_password
from app.modules.governance import log_event

router = APIRouter(prefix="/privacy", tags=["privacy"])

@router.get("/policy")
def policy():
    return {
        "principles": ["Minimización de datos", "Datos locales", "Exportación y eliminación"],
        "export": "GET /api/v1/backup/export",
        "delete_account": "POST /api/v1/privacy/delete-account",
    }

class DeleteIn(BaseModel):
    password: str
    confirm: str = Field(description='Must be DELETE')

@router.post("/delete-account")
def delete_account(body: DeleteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.confirm != "DELETE":
        raise HTTPException(400, 'confirm must be the string DELETE')
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(400, "Password incorrect")
    log_event(db, user.id, "user", "irreversible", "privacy.delete_account", True)
    uid = user.id
    db.delete(user)
    db.commit()
    return {"ok": True, "deleted_user_id": uid}
