"""Database engine and session dependency.

Default: SQLite at ./data/naijareview.db for dev/hackathon.
For production, set DATABASE_URL to a postgres:// connection string.

Usage in FastAPI routes:
    from naijareview.db.engine import get_session
    from sqlmodel import Session

    @router.post("/example")
    def example(session: Session = Depends(get_session)):
        ...
"""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from naijareview.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=settings.api_debug,
)


def create_db_and_tables() -> None:
    """Create all tables. Call once on startup."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session per request."""
    with Session(engine) as session:
        yield session
