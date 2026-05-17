"""Memory tools: load_user_history, save_review.

See §4.1 of INTERNAL_ARCHITECTURE.md.

These are LangChain ``@tool`` decorated functions that wrap the
``EpisodicMemory`` and ``FingerprintCache`` classes. They are the
canonical interface for agent nodes to interact with stored data.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool

from naijareview.config import settings
from naijareview.memory.episodic import EpisodicMemory
from naijareview.memory.semantic import FingerprintCache
from naijareview.schemas.user import Review, UserHistory

logger = logging.getLogger(__name__)

# Module-level singletons — initialised on first use
_episodic_memory: EpisodicMemory | None = None
_fingerprint_cache: FingerprintCache | None = None


def _get_episodic() -> EpisodicMemory:
    global _episodic_memory
    if _episodic_memory is None:
        _episodic_memory = EpisodicMemory(
            persist_dir=str(settings.chroma_persist_dir),
            collection_prefix=settings.chroma_collection_prefix,
        )
    return _episodic_memory


def _get_cache() -> FingerprintCache:
    global _fingerprint_cache
    if _fingerprint_cache is None:
        _fingerprint_cache = FingerprintCache()
    return _fingerprint_cache


# ── Tools ─────────────────────────────────────────────────────────────────────


@tool
def load_user_history(user_id: str) -> UserHistory:
    """Retrieve all reviews for a user from ChromaDB episodic memory.

    Performance budget: < 50ms for users with ≤ 500 reviews.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        UserHistory containing all reviews for this user.
        ``review_count`` will be 0 if no records exist — check
        ``has_sufficient_history`` to decide cold-start routing.

    Raises:
        No exception — returns empty UserHistory for missing users
        (caller decides if that's an error).
    """
    episodic = _get_episodic()
    history = episodic.load_user_history(user_id)
    logger.debug(
        "load_user_history(%s): %d reviews",
        user_id,
        history.review_count,
    )
    return history


@tool
def save_review(review: Review) -> bool:
    """Persist a new review to episodic memory (interactive demo only).

    Side effects: Writes to ChromaDB, invalidates fingerprint cache for user.

    Args:
        review: The Review object to persist.

    Returns:
        True if successfully saved.
    """
    episodic = _get_episodic()
    cache = _get_cache()

    try:
        episodic.add_review(review)
        cache.invalidate(review.user_id)
        logger.info(
            "Review %s saved, cache invalidated for user %s", review.review_id, review.user_id
        )
        return True
    except Exception as exc:
        logger.error("Failed to save review %s: %s", review.review_id, exc)
        return False


# ── Reset for testing ─────────────────────────────────────────────────────────


def _reset_singletons() -> None:
    """Reset module-level state. Used in tests only."""
    global _episodic_memory, _fingerprint_cache
    _episodic_memory = None
    _fingerprint_cache = None
