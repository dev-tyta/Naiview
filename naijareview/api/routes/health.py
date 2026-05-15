"""Health check endpoint — used by Docker, load balancers, and CI probes.

See §13.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter

from naijareview.config import settings

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    """Basic liveness probe. Returns 200 when the API process is running."""
    return {
        "status": "ok",
        "service": "naijareview",
        "version": "0.1.0",
    }


@router.get("/readyz")
async def readyz() -> dict:
    """Readiness probe — checks that critical dependencies are reachable.

    Returns 200 when the API and its backing services (DB, Chroma, etc.)
    are ready to accept traffic. Degraded components are reported but
    don't fail the probe (graceful degradation).
    """
    # TODO: ping ChromaDB, FAISS, Redis when wired
    return {
        "status": "ok",
        "service": "naijareview",
        "checks": {
            "database": "sqlite" if "sqlite" in settings.database_url else "postgres",
            "chromadb": "not_wired",
            "faiss": "not_wired",
            "fingerprint_cache": settings.cache_backend,
        },
    }
