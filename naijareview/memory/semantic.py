"""Semantic Memory — Fingerprint cache wrapper (Redis or in-memory).

See §10.2 of INTERNAL_ARCHITECTURE.md.
Key format: fingerprint:{user_id}
TTL: 24 hours; recomputed on miss.
"""

from __future__ import annotations


class FingerprintCache:
    """Cache for computed fingerprints — Redis in prod, dict in dev."""

    def __init__(self, backend: str = "memory", redis_url: str | None = None) -> None:
        self.backend = backend
        if backend == "redis" and redis_url:
            # TODO: Initialise Redis client
            pass
        self._memory_cache: dict[str, dict] = {}

    def get(self, user_id: str) -> dict | None:
        """Retrieve cached fingerprint if fresh."""
        # TODO: Implement — check cache_key freshness
        raise NotImplementedError

    def set(self, user_id: str, fingerprint: dict) -> None:
        """Store computed fingerprint."""
        # TODO: Implement
        raise NotImplementedError

    def invalidate(self, user_id: str) -> None:
        """Remove cached fingerprint (called after new review)."""
        # TODO: Implement
        raise NotImplementedError
