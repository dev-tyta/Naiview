"""Admin routes — development-only endpoints.

See §13.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/index-stats")
async def index_stats() -> dict:
    """Return Chroma + FAISS index counts."""
    # TODO: Implement
    return {"chroma_collections": 0, "faiss_items": 0}


@router.post("/rebuild-fingerprint/{user_id}")
async def rebuild_fingerprint(user_id: str) -> dict:
    """Force recompute a user's fingerprint."""
    # TODO: Implement
    return {"user_id": user_id, "status": "not_implemented"}
