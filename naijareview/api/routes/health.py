"""Health check endpoint.

See §13.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    """Basic health check."""
    return {"status": "ok", "service": "naijareview"}
