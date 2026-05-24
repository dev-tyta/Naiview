"""Health check endpoint — used by Docker, load balancers, and CI probes.

13.3 of INTERNAL_ARCHITECTURE.md.
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
    """Readiness probe — reflects actual warmup state of all components.

    Returns 200 regardless of component status (graceful degradation).
    Callers can inspect ``checks.ready`` to determine full readiness.
    """
    from naijareview.api.startup import get_status
    warmup = get_status()
    return {
        "status": "ready" if warmup["ready"] else "degraded",
        "service": "naijareview",
        "checks": {
            "database": "sqlite" if "sqlite" in settings.database_url else "postgres",
            "embedding_model": warmup["embedding"],
            "faiss_index": warmup["faiss"],
            "bm25_index": warmup["bm25"],
            "chromadb": warmup["chroma"],
            "task_a_graph": warmup["task_a_graph"],
            "task_b_graph": warmup["task_b_graph"],
            "fingerprint_cache": settings.cache_backend,
            "warmup_errors": warmup["errors"],
        },
    }
