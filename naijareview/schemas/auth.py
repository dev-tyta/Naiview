"""Auth and user account schemas.

Tracks authenticated users separately from review history.
user_id on UserAccount is the FK referenced by UserHistory,
Review, Fingerprint, and all state schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserAccount(BaseModel):
    """Authenticated user record.

    Stored in the user registry (separate from ChromaDB review history).
    user_id is the stable identifier propagated to all downstream schemas.

    Never store plaintext passwords here — only hashed_password via
    naijareview.utils.security.hash_password().
    OAuth users (google/github) have hashed_password = "".
    """

    user_id: str
    email: str
    display_name: str
    hashed_password: str
    created_at: datetime
    last_active_at: datetime | None = None
    is_active: bool = True
    auth_provider: Literal["local", "google", "github"] = "local"
    cultural_mode: Literal["general", "naija"] = "general"


class UserRegistration(BaseModel):
    """Payload for new user registration (local auth).

    Caller must hash password via hash_password() before creating UserAccount.
    """

    email: str
    display_name: str
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Payload for local auth login."""

    email: str
    password: str


class TokenPayload(BaseModel):
    """Claims carried inside a JWT.

    sub = user_id. Validate exp before trusting any other field.
    """

    sub: str
    exp: int
    iat: int
    display_name: str


class TokenResponse(BaseModel):
    """Returned to client on successful auth."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    display_name: str


class UserSession(BaseModel):
    """Server-side session record (optional — for revocation tracking)."""

    session_id: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False
