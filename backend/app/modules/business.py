"""BUSINESS OS — clients & invoices (separate from personal ledger)."""
from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Client, Invoice
from app.domain.finance_service import portfolio_summary
from app.modules.governance import log_event

router = APIRouter(prefix="/business", tags=["business"])

class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = None
    notes: Optional[str] = None

class InvoiceIn(BaseModel):
    client_id: Optional[int] = None
    number: str = Field(min_length=1, max_length=64)
    amount: Decimal = Field(gt=0)
    status: str = "draft"
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    description: Optional[str] = None

@router.get("/summary")
def business_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ledger = portfolio_summary(db, user.id, "business")
    clients_n = db.scalar(select(func.count()).select_from(Client).where(Client.user_id == user.id, Client.is_active.is_(True))) or 0
    inv = db.scalars(select(Invoice).where(Invoice.user_id == user.id)).all()
    paid = sum(float(i.amount) for i in inv if i.status == "paid")
    open_amt = sum(float(i.amount) for i in inv if i.status in ("draft", "sent"))
    return {"clients_active": clients_n, "invoices_count": len(inv), "invoices_paid_total": paid, "invoices_open_total": open_amt, "business_ledger": ledger}

@router.get("/clients")
def list_clients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Client).where(Client.user_id == user.id)).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "is_active": c.is_active} for c in rows]

@router.post("/clients", status_code=201)
def create_client(body: ClientIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = Client(user_id=user.id, name=body.name.strip(), email=body.email, notes=body.notes)
    db.add(c)
    log_event(db, user.id, "user", "reversible", "business.client_create", True)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}

@router.get("/invoices")
def list_invoices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Invoice).where(Invoice.user_id == user.id).order_by(Invoice.id.desc())).all()
    return [{"id": i.id, "number": i.number, "amount": float(i.amount), "status": i.status, "client_id": i.client_id} for i in rows]

@router.post("/invoices", status_code=201)
def create_invoice(body: InvoiceIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.status not in ("draft", "sent", "paid", "cancelled"):
        raise HTTPException(400, "invalid status")
    if body.client_id:
        c = db.get(Client, body.client_id)
        if not c or c.user_id != user.id:
            raise HTTPException(404, "Client not found")
    inv = Invoice(user_id=user.id, client_id=body.client_id, number=body.number.strip(), amount=body.amount, status=body.status, issue_date=body.issue_date or date.today(), due_date=body.due_date, description=body.description)
    db.add(inv)
    log_event(db, user.id, "user", "reversible", "business.invoice_create", True)
    db.commit()
    db.refresh(inv)
    return {"id": inv.id, "number": inv.number, "status": inv.status}

@router.patch("/invoices/{invoice_id}")
def update_invoice_status(invoice_id: int, status: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.user_id != user.id:
        raise HTTPException(404, "Not found")
    if status not in ("draft", "sent", "paid", "cancelled"):
        raise HTTPException(400, "invalid status")
    inv.status = status
    db.commit()
    return {"id": inv.id, "status": inv.status}
