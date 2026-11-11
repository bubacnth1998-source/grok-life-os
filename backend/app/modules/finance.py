from datetime import date as date_cls
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import User, Account, LedgerTransaction, Posting
from app.domain.finance_service import portfolio_summary, record_simple, account_balance
from app.domain.events import publish

router = APIRouter(prefix="/finance", tags=["finance"])

class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    currency: str = "EUR"
    ledger_scope: str = "personal"
    is_reserved: bool = False

class TxIn(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    kind: str
    description: str = Field(min_length=1, max_length=400)
    category: str | None = None
    date: Optional[date_cls] = None
    ledger_scope: str = "personal"

@router.get("/summary")
def summary(scope: str = "personal", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if scope not in ("personal", "business"):
        raise HTTPException(400, "scope must be personal or business")
    return portfolio_summary(db, user.id, scope)

@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Account).where(Account.user_id == user.id, Account.is_active.is_(True))).all()
    return [{"id": a.id, "name": a.name, "currency": a.currency, "ledger_scope": a.ledger_scope, "is_reserved": a.is_reserved, "balance": float(account_balance(db, a.id))} for a in rows]

@router.post("/accounts", status_code=201)
def create_account(body: AccountIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.ledger_scope not in ("personal", "business"):
        raise HTTPException(400, "invalid ledger_scope")
    a = Account(user_id=user.id, name=body.name.strip(), currency=body.currency, ledger_scope=body.ledger_scope, is_reserved=body.is_reserved)
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "name": a.name}

@router.post("/transactions", status_code=201)
def create_tx(body: TxIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.kind not in ("income", "expense"):
        raise HTTPException(400, "kind must be income or expense")
    try:
        tx = record_simple(db, user.id, body.account_id, body.amount, body.kind, body.description, body.category, body.date or date_cls.today(), body.ledger_scope)
    except ValueError as e:
        raise HTTPException(400, str(e))
    publish("finance.transaction_created", {"user_id": user.id, "tx_id": tx.id, "kind": body.kind})
    return {"id": tx.id, "kind": tx.kind, "description": tx.description}

@router.get("/transactions")
def list_tx(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(LedgerTransaction).where(LedgerTransaction.user_id == user.id).order_by(LedgerTransaction.date.desc()).limit(min(limit, 200))).all()
    out = []
    for t in rows:
        posts = db.scalars(select(Posting).where(Posting.transaction_id == t.id)).all()
        out.append({"id": t.id, "date": t.date.isoformat(), "description": t.description, "category": t.category, "kind": t.kind, "scope": t.ledger_scope, "postings": [{"account_id": p.account_id, "amount": float(p.amount)} for p in posts]})
    return out
