"""Eval metric — NDCG@k.

Computes Normalised Discounted Cumulative Gain at k for ranking quality.
Uses ``sklearn.metrics.ndcg_score``.

Usage:
    from naijareview.eval.metrics.ndcg import compute_ndcg_at_k

    score = compute_ndcg_at_k(predicted_item_ids, true_item_ids, k=10)
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def compute_ndcg_at_k(
    predicted_item_ids: list[str],
    true_item_ids: list[str],
    k: int = 10,
) -> float:
    """Compute NDCG@k for ranking quality.

    Treats true_item_ids as binary relevance: items in the true set
    get relevance 1, everything else gets 0.

    Args:
        predicted_item_ids: Ranked list of item IDs from the recommender.
        true_item_ids: List of relevant item IDs (ground truth).
        k: Cutoff rank (default 10).

    Returns:
        NDCG@k score in [0, 1], or 0.0 on error.
    """
    if not predicted_item_ids or not true_item_ids:
        return 0.0

    try:
        from sklearn.metrics import ndcg_score

        k = min(k, len(predicted_item_ids))
        if k == 0:
            return 0.0

        true_set = set(true_item_ids)
        n_items = len(predicted_item_ids)

        # True relevance: 1 for relevant items, 0 otherwise
        y_true = np.zeros((1, n_items))
        y_score = np.zeros((1, n_items))

        for i, item_id in enumerate(predicted_item_ids):
            y_true[0, i] = 1.0 if item_id in true_set else 0.0
            # Score is inverse rank (higher rank = lower score)
            y_score[0, i] = 1.0 / (i + 1)

        return float(ndcg_score(y_true, y_score, k=k))
    except ImportError:
        logger.warning("scikit-learn not installed. Install with: pip install scikit-learn")
        return 0.0
    except Exception as exc:
        logger.warning("NDCG computation failed: %s", exc)
        return 0.0
