"""Password hashing, verification, and JWT utilities.

Usage:
    from naijareview.utils.security import (
        hash_password, verify_password,
        create_access_token, decode_access_token,
    )

    hashed = hash_password("hunter2")
    ok     = verify_password("hunter2", hashed)      # True
    token  = create_access_token(user_id, display_name)
    claims = decode_access_token(token)               # TokenPayload or raises
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from naijareview.config import settings
from naijareview.schemas.auth import TokenPayload

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ─────────────────────────────────────────────────────────────────

def hash_password(plaintext: str) -> str:
    """Return a bcrypt hash of *plaintext*. Store the return value, never the input."""
    return _ctx.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True if *plaintext* matches *hashed*. Timing-safe comparison."""
    return _ctx.verify(plaintext, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, display_name: str) -> str:
    """Create a signed JWT for *user_id*.

    Expiry is controlled by settings.jwt_expire_minutes.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "display_name": display_name,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT. Raises JWTError if invalid or expired.

    Callers should catch JWTError and return HTTP 401.
    """
    raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return TokenPayload(
        sub=raw["sub"],
        exp=raw["exp"],
        iat=raw["iat"],
        display_name=raw.get("display_name", ""),
    )
