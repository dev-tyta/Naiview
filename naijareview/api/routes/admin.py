"""Admin routes — development-only endpoints for debugging and introspection.

13.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter

from naijareview.config import settings

router = APIRouter()


@router.get("/health")
async def admin_health() -> dict:
    """Detailed health check — component status."""
    return {
        "status": "ok",
        "service": "naijareview",
        "version": "0.1.0",
        "mode": "hackathon",
        "components": {
            "gemini_api": "not_checked",  # TODO: ping Gemini health endpoint
            "chromadb": "stub",
            "faiss": "stub",
            "fingerprint_cache": settings.cache_backend,
        },
    }


@router.get("/index-stats")
async def index_stats() -> dict:
    """Return Chroma + FAISS index counts and cache stats."""
    # TODO: query real backends when wired
    return {
        "chroma_collections": 0,
        "faiss_items": 0,
        "users_cached": 0,
        "cache_backend": settings.cache_backend,
        "cache_ttl_hours": settings.fingerprint_cache_ttl_hours,
    }


@router.post("/rebuild-fingerprint/{user_id}")
async def rebuild_fingerprint(user_id: str) -> dict:
    """Force recompute a user's behavioural fingerprint."""
    # TODO: call FingerprintBuilder.invalidate() then get_or_build()
    return {
        "user_id": user_id,
        "status": "not_implemented",
        "note": "Set GEMINI_API_KEY and wire ChromaDB to enable",
    }


@router.get("/config")
async def admin_config() -> dict:
    """Return non-sensitive config values for debugging."""
    return {
        "api_debug": settings.api_debug,
        "cache_backend": settings.cache_backend,
        "generation_model": settings.gemini_generation_model,
        "utility_model": settings.gemini_utility_model,
        "vibe_regen_threshold": settings.vibe_regen_threshold,
        "vibe_max_retries": settings.vibe_max_retries,
        "retrieval_top_k": settings.retrieval_top_k,
        "bm25_weight": settings.bm25_weight,
        "semantic_weight": settings.semantic_weight,
        "task_b_confidence_threshold": settings.task_b_confidence_threshold,
        "min_diversity_score": settings.min_diversity_score,
        "min_history_for_fingerprint": settings.min_history_for_fingerprint,
    }
