"""Auth routes — register, login, logout, current user.

POST /auth/register  → create account, return token
POST /auth/login     → verify credentials, return token
POST /auth/logout    → revoke session
GET  /auth/me        → return current user info
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session, select

from naijareview.config import settings
from naijareview.db.engine import get_session
from naijareview.db.models import SessionDB, UserDB
from naijareview.schemas.auth import TokenResponse, UserLogin, UserRegistration
from naijareview.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter()
_bearer = HTTPBearer()


# ── Dependency — authenticated user ──────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: Session = Depends(get_session),
) -> UserDB:
    """FastAPI dependency — validate JWT and return the UserDB record.

    Usage:
        @router.get("/protected")
        def endpoint(user: UserDB = Depends(get_current_user)):
            ...
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise credentials_error

    # Check session not revoked
    db_session = session.exec(
        select(SessionDB).where(
            SessionDB.user_id == payload.sub,
            SessionDB.revoked == False,  # noqa: E712
        )
    ).first()
    if db_session is None:
        raise credentials_error

    user = session.get(UserDB, payload.sub)
    if user is None or not user.is_active:
        raise credentials_error

    return user


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegistration, session: Session = Depends(get_session)) -> TokenResponse:
    """Create a new local account and return an access token."""
    existing = session.exec(select(UserDB).where(UserDB.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user = UserDB(
        user_id=user_id,
        email=body.email,
        display_name=body.display_name,
        hashed_password=hash_password(body.password),
    )
    session.add(user)

    token = create_access_token(user_id, body.display_name)
    _create_session(session, user_id)
    session.commit()

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user_id=user_id,
        display_name=body.display_name,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, session: Session = Depends(get_session)) -> TokenResponse:
    """Authenticate with email + password and return an access token."""
    user = session.exec(select(UserDB).where(UserDB.email == body.email)).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    token = create_access_token(user.user_id, user.display_name)
    _create_session(session, user.user_id)

    user.last_active_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user_id=user.user_id,
        display_name=user.display_name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    """Revoke all active sessions for the current user."""
    active_sessions = session.exec(
        select(SessionDB).where(
            SessionDB.user_id == user.user_id,
            SessionDB.revoked == False,  # noqa: E712
        )
    ).all()
    for s in active_sessions:
        s.revoked = True
        session.add(s)
    session.commit()


@router.get("/me")
def me(user: UserDB = Depends(get_current_user)) -> dict:
    """Return the authenticated user's profile."""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "display_name": user.display_name,
        "auth_provider": user.auth_provider,
        "cultural_mode": user.cultural_mode,
        "created_at": user.created_at,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _create_session(session: Session, user_id: str) -> None:
    db_session = SessionDB(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    )
    session.add(db_session)
