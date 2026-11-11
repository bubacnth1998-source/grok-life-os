from __future__ import annotations
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.domain.models import Account, Posting, LedgerTransaction

def account_balance(db: Session, account_id: int) -> Decimal:
    total = db.scalar(select(func.coalesce(func.sum(Posting.amount), 0)).where(Posting.account_id == account_id))
    return Decimal(total or 0)

def portfolio_summary(db: Session, user_id: int, scope: str = "personal") -> dict:
    accounts = db.scalars(select(Account).where(Account.user_id == user_id, Account.is_active.is_(True), Account.ledger_scope == scope)).all()
    available = Decimal("0")
    reserved = Decimal("0")
    detail = []
    for a in accounts:
        bal = account_balance(db, a.id)
        detail.append({"id": a.id, "name": a.name, "balance": float(bal), "is_reserved": a.is_reserved, "currency": a.currency})
        if a.is_reserved:
            reserved += bal
        else:
            available += bal
    return {"scope": scope, "available": float(available), "reserved": float(reserved), "total": float(available + reserved), "accounts": detail}

def record_simple(db, user_id, account_id, amount, kind, description, category, day, scope="personal"):
    acc = db.get(Account, account_id)
    if not acc or acc.user_id != user_id:
        raise ValueError("Account not found")
    signed = -abs(amount) if kind == "expense" else abs(amount)
    if kind not in ("income", "expense"):
        raise ValueError("kind must be income or expense")
    tx = LedgerTransaction(user_id=user_id, date=day, description=description, category=category, kind=kind, ledger_scope=scope)
    db.add(tx)
    db.flush()
    db.add(Posting(transaction_id=tx.id, account_id=account_id, amount=signed))
    db.commit()
    db.refresh(tx)
    return tx
