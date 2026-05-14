"""Memory tools: load_user_history, save_review.

See §4.1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.user import Review, UserHistory


@tool
def load_user_history(user_id: str) -> UserHistory:
    """Retrieve all reviews for a user from ChromaDB episodic memory.

    Performance budget: < 50ms for users with ≤ 500 reviews.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        UserHistory containing all reviews for this user.

    Raises:
        UserNotFoundError: If user_id has no records — caller routes to cold-start flow.
    """
    # TODO: Implement ChromaDB retrieval — Aaliyah owns retrieval stack
    raise NotImplementedError("load_user_history not yet implemented")


@tool
def save_review(review: Review) -> bool:
    """Persist a new review to episodic memory (interactive demo only).

    Side effects: Writes to ChromaDB, invalidates fingerprint cache for user.

    Args:
        review: The Review object to persist.

    Returns:
        True if successfully saved.
    """
    # TODO: Implement ChromaDB write + cache invalidation
    raise NotImplementedError("save_review not yet implemented")
