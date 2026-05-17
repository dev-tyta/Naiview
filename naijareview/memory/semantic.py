"""Semantic Memory — Fingerprint cache wrapper (Redis or in-memory).

Owner: Aaliyah
See §10.2 of INTERNAL_ARCHITECTURE.md.

Key format: ``fingerprint:{user_id}``
TTL: 24 hours (configurable via ``settings.fingerprint_cache_ttl_hours``).
Recomputed on cache miss or explicit invalidation.

Backend: ``memory`` uses a Python dict (dev/hackathon).
         ``redis`` uses Redis (production).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from naijareview.config import settings
from naijareview.schemas.user import Fingerprint

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "fingerprint:"


class FingerprintCache:
    """Cache for computed behavioural fingerprints.

    Usage:
        cache = FingerprintCache()  # in-memory by default
        fp = cache.get("user_001")  # → Fingerprint or None

        cache.set("user_001", fingerprint)
        cache.invalidate("user_001")
    """

    def __init__(
        self,
        backend: str | None = None,
        redis_url: str | None = None,
        ttl_hours: int | None = None,
    ) -> None:
        self.backend = backend or settings.cache_backend
        self.ttl_hours = ttl_hours or settings.fingerprint_cache_ttl_hours
        self._memory_cache: dict[str, tuple[float, bytes]] = {}  # key → (expiry_ts, serialized)
        self._redis_client: Any = None

        if self.backend == "redis":
            self._init_redis(redis_url or settings.redis_url)

    # ── Public API ───────────────────────────────────────────────────────

    def get(self, user_id: str) -> Fingerprint | None:
        """Retrieve a cached fingerprint, or None if missing / expired."""
        key = f"{_CACHE_PREFIX}{user_id}"

        if self.backend == "redis":
            return self._redis_get(key)

        return self._memory_get(key)

    def set(self, user_id: str, fingerprint: Fingerprint) -> None:
        """Store a computed fingerprint in the cache."""
        key = f"{_CACHE_PREFIX}{user_id}"
        serialized = fingerprint.model_dump_json().encode("utf-8")

        if self.backend == "redis":
            self._redis_set(key, serialized)
        else:
            self._memory_set(key, serialized)

    def invalidate(self, user_id: str) -> None:
        """Remove a cached fingerprint. Called after a new review is saved."""
        key = f"{_CACHE_PREFIX}{user_id}"
        if self.backend == "redis":
            if self._redis_client:
                self._redis_client.delete(key)
                logger.debug("Cache invalidated (redis): %s", key)
        else:
            self._memory_cache.pop(key, None)
            logger.debug("Cache invalidated (memory): %s", key)

    # ── In-memory backend ────────────────────────────────────────────────

    def _memory_get(self, key: str) -> Fingerprint | None:
        entry = self._memory_cache.get(key)
        if entry is None:
            return None
        expiry, serialized = entry
        if datetime.now(timezone.utc).timestamp() > expiry:
            self._memory_cache.pop(key, None)
            return None
        return Fingerprint.model_validate_json(serialized)

    def _memory_set(self, key: str, serialized: bytes) -> None:
        expiry = datetime.now(timezone.utc).timestamp() + (self.ttl_hours * 3600)
        self._memory_cache[key] = (expiry, serialized)

    # ── Redis backend ────────────────────────────────────────────────────

    def _init_redis(self, redis_url: str) -> None:
        try:
            import redis as _redis

            self._redis_client = _redis.from_url(redis_url, decode_responses=False)
            self._redis_client.ping()
            logger.info("Connected to Redis at %s", redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable, falling back to memory cache: %s", exc)
            self.backend = "memory"

    def _redis_get(self, key: str) -> Fingerprint | None:
        if self._redis_client is None:
            return None
        try:
            raw = self._redis_client.get(key)
            if raw is None:
                return None
            return Fingerprint.model_validate_json(raw)
        except Exception as exc:
            logger.warning("Redis get failed for %s: %s", key, exc)
            return None

    def _redis_set(self, key: str, serialized: bytes) -> None:
        if self._redis_client is None:
            return
        try:
            self._redis_client.setex(key, self.ttl_hours * 3600, serialized)
        except Exception as exc:
            logger.warning("Redis set failed for %s: %s", key, exc)

    # ── Utility ──────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        """Number of entries in the cache (memory backend only)."""
        if self.backend == "memory":
            now = datetime.now(timezone.utc).timestamp()
            # Purge expired entries on read
            active = sum(1 for v in self._memory_cache.values() if v[0] > now)
            return active
        return -1  # Redis doesn't expose this cheaply
