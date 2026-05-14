"""SQLModel table models for the relational store.

Only auth and session data lives here. Review history → ChromaDB (episodic memory).
Fingerprint cache → Redis/in-memory (semantic memory).

Enum-like fields use plain `str` columns — validation is handled at the Pydantic
schema layer (Literal types in schemas/auth.py). This avoids SQLEnum migration pain
when valid values need to change.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserDB(SQLModel, table=True):
    """Persisted user account. Maps 1-to-1 with schemas.auth.UserAccount.

    auth_provider values: "local" | "google" | "github"  (str, not SQLEnum)
    cultural_mode values: "general" | "naija"             (str, not SQLEnum)
    """

    __tablename__ = "users"

    user_id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    display_name: str
    hashed_password: str
    is_active: bool = True
    auth_provider: str = "local"
    cultural_mode: str = "general"
    created_at: datetime = Field(default_factory=_utcnow)
    last_active_at: Optional[datetime] = None


class SessionDB(SQLModel, table=True):
    """Persisted JWT session — used for token revocation.

    Check `revoked` before accepting any token. On logout, flip revoked=True.
    """

    __tablename__ = "sessions"

    session_id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True)
    issued_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime
    revoked: bool = False
