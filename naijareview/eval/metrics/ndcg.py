"""Eval metric stubs — NDCG@k."""

from __future__ import annotations


def compute_ndcg_at_k(predicted_rankings: list, true_relevance: list, k: int = 10) -> float:
    """Compute NDCG@k for ranking quality."""
    # TODO: Implement using sklearn.metrics.ndcg_score
    raise NotImplementedError
