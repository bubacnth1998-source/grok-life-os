"""Export / import — portable, integrity-checked recovery."""
import hashlib
import hmac
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user
from app.domain.models import (
    User, MemoryItem, Project, Task, Habit, Account,
    LedgerTransaction, Posting,
)

router = APIRouter(prefix="/backup", tags=["backup"])


def _rows(db: Session, model, user_id: int):
    return db.scalars(select(model).where(model.user_id == user_id)).all()


@router.get("/export")
def export_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    accounts = _rows(db, Account, user.id)
    projects = _rows(db, Project, user.id)
    transactions = _rows(db, LedgerTransaction, user.id)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "app": "grok-life-os",
        "version": "0.2.0",
        "user": {"email": user.email, "full_name": user.full_name},
        "memory": [{"kind": m.kind, "title": m.title, "content": m.content, "confidence": m.confidence, "tags": m.tags} for m in _rows(db, MemoryItem, user.id)],
        "projects": [{"id": p.id, "name": p.name, "description": p.description, "status": p.status, "progress": p.progress, "priority": p.priority} for p in projects],
        "tasks": [{"title": t.title, "status": t.status, "priority": t.priority, "project_id": t.project_id} for t in _rows(db, Task, user.id)],
        "habits": [{"name": h.name, "frequency": h.frequency, "is_active": h.is_active} for h in _rows(db, Habit, user.id)],
        "accounts": [{"id": a.id, "name": a.name, "currency": a.currency, "ledger_scope": a.ledger_scope, "is_reserved": a.is_reserved, "is_active": a.is_active, "notes": a.notes} for a in accounts],
        "transactions": [
            {
                "date": t.date.isoformat(),
                "description": t.description,
                "category": t.category,
                "kind": t.kind,
                "ledger_scope": t.ledger_scope,
                "postings": [
                    {"account_id": p.account_id, "amount": str(p.amount)}
                    for p in db.scalars(select(Posting).where(Posting.transaction_id == t.id)).all()
                ],
            }
            for t in transactions
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["integrity"] = {"algo": "sha256", "hex": hashlib.sha256(raw.encode()).hexdigest()}
    return payload


@router.post("/import")
def import_data(body: dict = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not isinstance(body, dict):
        raise HTTPException(400, "Backup must be a JSON object")

    # Exports created by this app carry a checksum. Reject tampered files before
    # writing anything; checksum-free partial imports remain supported.
    integrity = body.get("integrity")
    if integrity is not None:
        if not isinstance(integrity, dict) or integrity.get("algo") != "sha256" or not isinstance(integrity.get("hex"), str):
            raise HTTPException(400, "Invalid backup integrity metadata")
        unsigned = {k: v for k, v in body.items() if k != "integrity"}
        raw = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(raw.encode()).hexdigest()
        if not hmac.compare_digest(expected, integrity["hex"]):
            raise HTTPException(400, "Backup integrity check failed")

    collections = ("memory", "projects", "tasks", "habits", "accounts", "transactions")
    for key in collections:
        if key in body and not isinstance(body[key], list):
            raise HTTPException(400, f"{key} must be an array")

    created = {key: 0 for key in collections}
    account_ids: dict[int, int] = {}
    project_ids: dict[int, int] = {}
    try:
        for item in body.get("accounts", []):
            if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                raise HTTPException(400, "Each account requires a name")
            scope = item.get("ledger_scope", "personal")
            if scope not in ("personal", "business"):
                raise HTTPException(400, "Invalid account ledger_scope")
            account = Account(
                user_id=user.id, name=str(item["name"]).strip()[:120],
                currency=str(item.get("currency", "EUR"))[:8], ledger_scope=scope,
                is_reserved=bool(item.get("is_reserved", False)),
                is_active=bool(item.get("is_active", True)), notes=item.get("notes"),
            )
            db.add(account)
            db.flush()
            if item.get("id") is not None:
                account_ids[int(item["id"])] = account.id
            created["accounts"] += 1

        for item in body.get("projects", []):
            if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                raise HTTPException(400, "Each project requires a name")
            project = Project(
                user_id=user.id, name=str(item["name"]).strip()[:200],
                description=item.get("description"), status=str(item.get("status", "active"))[:32],
                progress=max(0, min(100, int(item.get("progress") or 0))),
                priority=str(item.get("priority", "medium"))[:16],
            )
            db.add(project)
            db.flush()
            if item.get("id") is not None:
                project_ids[int(item["id"])] = project.id
            created["projects"] += 1

        for item in body.get("memory", []):
            if not isinstance(item, dict) or not str(item.get("title", "")).strip():
                raise HTTPException(400, "Each memory item requires a title")
            db.add(MemoryItem(
                user_id=user.id, kind=str(item.get("kind", "fact"))[:64],
                title=str(item["title"]).strip()[:300], content=item.get("content"),
                confidence=str(item.get("confidence", "confirmed"))[:32],
                source="import", tags=item.get("tags"),
            ))
            created["memory"] += 1

        for item in body.get("tasks", []):
            if not isinstance(item, dict) or not str(item.get("title", "")).strip():
                raise HTTPException(400, "Each task requires a title")
            old_project_id = item.get("project_id")
            db.add(Task(
                user_id=user.id, title=str(item["title"]).strip()[:300],
                status=str(item.get("status", "todo"))[:32],
                priority=str(item.get("priority", "medium"))[:16],
                project_id=project_ids.get(int(old_project_id)) if old_project_id is not None else None,
            ))
            created["tasks"] += 1

        for item in body.get("habits", []):
            if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                raise HTTPException(400, "Each habit requires a name")
            db.add(Habit(
                user_id=user.id, name=str(item["name"]).strip()[:150],
                frequency=str(item.get("frequency", "daily"))[:32],
                is_active=bool(item.get("is_active", True)),
            ))
            created["habits"] += 1

        for item in body.get("transactions", []):
            if not isinstance(item, dict):
                raise HTTPException(400, "Invalid transaction")
            kind = item.get("kind")
            if kind not in ("income", "expense"):
                raise HTTPException(400, "Invalid transaction kind")
            postings = item.get("postings")
            if not isinstance(postings, list) or not postings:
                raise HTTPException(400, "Transaction requires postings")
            tx = LedgerTransaction(
                user_id=user.id, date=date.fromisoformat(item["date"]),
                description=str(item.get("description", ""))[:400],
                category=item.get("category"), kind=kind,
                ledger_scope=str(item.get("ledger_scope", "personal"))[:16],
            )
            db.add(tx)
            db.flush()
            for posting in postings:
                if not isinstance(posting, dict):
                    raise HTTPException(400, "Invalid transaction posting")
                old_account_id = int(posting["account_id"])
                new_account_id = account_ids.get(old_account_id)
                if new_account_id is None:
                    raise HTTPException(400, "Transaction references an account not included in this backup")
                amount = Decimal(str(posting["amount"]))
                db.add(Posting(transaction_id=tx.id, account_id=new_account_id, amount=amount))
            created["transactions"] += 1

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except (ValueError, TypeError, KeyError, InvalidOperation) as exc:
        db.rollback()
        raise HTTPException(400, f"Invalid backup data: {exc}") from exc
    except Exception:
        db.rollback()
        raise

    return {"ok": True, "created": created}
