"""FastAPI dependencies — agent resolver, auth, and shared deps.

Provides:
- ``get_agent`` — returns an AgentProtocol implementation (stub by default,
  real agent when LangGraph graphs are wired in)
- ``get_optional_user`` — JWT-protected user that returns None instead of 401
- ``get_session`` — re-exported from db.engine
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from naijareview.db.engine import get_session as _get_session
from naijareview.eval.harness import AgentProtocol, StubAgent

_bearer = HTTPBearer(auto_error=False)


# ── Agent resolver ───────────────────────────────────────────────────────────


def get_agent() -> AgentProtocol:
    """Return the agent implementation.

    Currently returns ``StubAgent``. When the real LangGraph agents are wired,
    replace this with a resolver that switches on route context or config.
    """
    return StubAgent()


# ── Current user (optional auth) ─────────────────────────────────────────────


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(_get_session),
) -> object | None:
    """Like ``get_current_user`` but returns ``None`` instead of 401.

    Used by routes where auth is optional (e.g. cold-start Task B where
    there may be no user_id yet).
    """
    if credentials is None:
        return None
    from naijareview.api.routes.auth import get_current_user as _guard

    try:
        return _guard(credentials, session)
    except Exception:
        return None


# ── Re-export for convenience ────────────────────────────────────────────────
get_session = _get_session
