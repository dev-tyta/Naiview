"""Reasoning tools: analyse_item_for_user, rerank_candidates.

See §4.5 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.item import Item, RankedItem
from naijareview.schemas.user import Fingerprint


@tool
def analyse_item_for_user(item: Item, fingerprint: Fingerprint) -> dict:
    """LLM-backed analysis of how an item maps to a user's preferences.

    Used in Task A before generation.
    LLM tier: Haiku (utility task).

    Args:
        item: The item to analyse.
        fingerprint: The user's behavioural fingerprint.

    Returns:
        Dict with keys: inferred_sentiment, relevant_topics,
        predicted_rating_range, reasoning.
    """
    # TODO: Implement — Testimony owns Agent A
    raise NotImplementedError("analyse_item_for_user not yet implemented")


@tool
def rerank_candidates(
    candidates: list[Item],
    fingerprint: Fingerprint,
    context_query: str,
) -> list[RankedItem]:
    """LLM-backed chain-of-thought reranking of top-20 candidates.

    LLM tier: Sonnet 4 (quality-critical).

    Args:
        candidates: Top-20 candidate items from retrieval.
        fingerprint: The user's behavioural fingerprint.
        context_query: What the user wants right now.

    Returns:
        List of RankedItems sorted by alignment_score descending.
    """
    # TODO: Implement — Aaliyah owns Agent B
    raise NotImplementedError("rerank_candidates not yet implemented")
