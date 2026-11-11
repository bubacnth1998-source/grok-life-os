from __future__ import annotations

import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.domain.models import User, AuditLog
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# In-process failed-login tracker (per process). Not shared across serverless
# instances; still reduces casual password spraying on a single instance.
_failed_logins: dict[str, list[float]] = defaultdict(list)
_MAX_FAILED = 8
_WINDOW_SEC = 300


def _prune_failures(email: str, now: float) -> list[float]:
    recent = [t for t in _failed_logins[email] if now - t < _WINDOW_SEC]
    _failed_logins[email] = recent
    return recent


def _register_failure(email: str) -> None:
    now = time.time()
    recent = _prune_failures(email, now)
    recent.append(now)
    _failed_logins[email] = recent


def _clear_failures(email: str) -> None:
    _failed_logins.pop(email, None)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name.strip(),
    )
    db.add(user)
    db.flush()  # assign user.id before audit row
    # Privacy: bind audit to user_id only; never store email in detail
    db.add(AuditLog(user_id=user.id, action="user.register", detail=None))
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    now = time.time()
    recent = _prune_failures(email, now)
    if len(recent) >= _MAX_FAILED:
        raise HTTPException(429, "Too many failed login attempts; try again later")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        _register_failure(email)
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(401, "User inactive")

    _clear_failures(email)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
