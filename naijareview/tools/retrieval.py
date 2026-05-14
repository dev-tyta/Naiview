"""Retrieval tools: retrieve_similar_items, retrieve_candidates_hybrid.

See §4.4 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.item import Item
from naijareview.schemas.user import ColdStartPersona, Fingerprint


@tool
def retrieve_similar_items(
    query: str,
    category: str | None = None,
    top_k: int = 20,
) -> list[Item]:
    """Semantic search over FAISS item index, filtered by category.

    Backend: FAISS flat IP index; query embedded with all-MiniLM-L6-v2.
    Post-filter by category if provided.

    Args:
        query: Search query text.
        category: Optional category filter.
        top_k: Number of items to return (default 20).

    Returns:
        List of matching Items.
    """
    # TODO: Implement — Aaliyah owns retrieval stack
    raise NotImplementedError("retrieve_similar_items not yet implemented")


@tool
def retrieve_candidates_hybrid(
    query: str,
    fingerprint: Fingerprint | None = None,
    cold_start_persona: ColdStartPersona | None = None,
    top_k: int = 20,
) -> list[Item]:
    """Hybrid BM25 + semantic retrieval for Task B candidate generation.

    Algorithm:
    1. BM25 query from query + top topic_focus words from fingerprint.
    2. Semantic query from embedded query.
    3. Retrieve top-30 from each, deduplicate by item_id.
    4. Re-score: 0.4 × bm25 + 0.6 × semantic, return top-20.

    Args:
        query: Search query text.
        fingerprint: Optional user fingerprint for query enrichment.
        cold_start_persona: Optional cold-start persona for new users.
        top_k: Number of candidates to return (default 20).

    Returns:
        List of candidate Items.
    """
    # TODO: Implement — Aaliyah owns retrieval stack
    raise NotImplementedError("retrieve_candidates_hybrid not yet implemented")
