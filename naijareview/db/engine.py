"""Database engine and session dependency.

PostgreSQL is optional. If DATABASE_URL is a placeholder (contains 'PASSWORD'
or 'HOST') the DB is disabled and all DB operations become no-ops.

Set DATABASE_URL to a real postgres:// string in .env to enable auth features.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from naijareview.config import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_MARKERS = ("PASSWORD", "HOST.railway")

def _db_enabled() -> bool:
    url = settings.database_url
    return not any(m in url for m in _PLACEHOLDER_MARKERS)


# Only create the engine when the URL is real — avoids psycopg2 connection
# errors on startup when using the placeholder DATABASE_URL.
_engine = None

if _db_enabled():
    try:
        from sqlmodel import create_engine as _create_engine
        _engine = _create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
            echo=settings.api_debug,
        )
    except Exception as exc:
        logger.warning("DB engine init failed: %s — DB disabled", exc)


def create_db_and_tables() -> None:
    """Create all tables. No-op when DATABASE_URL is a placeholder."""
    if _engine is None:
        logger.info("DB not configured — skipping create_db_and_tables()")
        return
    try:
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(_engine)
    except Exception as exc:
        logger.warning("create_db_and_tables failed: %s", exc)


def get_session() -> Generator:
    """FastAPI dependency — yields a DB session, or None when DB is disabled."""
    if _engine is None:
        yield None
        return
    from sqlmodel import Session
    with Session(_engine) as session:
        yield session
