"""Episodic Memory — ChromaDB wrapper for user review history.

Owner: Aaliyah
See §10.1 of INTERNAL_ARCHITECTURE.md.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim).
Read patterns: load_user_history, retrieve_similar within user.
Write patterns: Append-only.
"""

from __future__ import annotations


class EpisodicMemory:
    """ChromaDB-backed episodic memory for user review histories."""

    def __init__(self, persist_dir: str, collection_prefix: str) -> None:
        self.persist_dir = persist_dir
        self.collection_prefix = collection_prefix
        # TODO: Initialise ChromaDB client and collection

    def load_user_history(self, user_id: str) -> dict:
        """Fetch all reviews for a user."""
        # TODO: Implement
        raise NotImplementedError

    def retrieve_similar(self, user_id: str, query_embedding: list[float], k: int = 5) -> list:
        """Semantic search within a user's review history."""
        # TODO: Implement
        raise NotImplementedError

    def add_review(self, review: dict) -> None:
        """Append a new review to episodic memory."""
        # TODO: Implement
        raise NotImplementedError
