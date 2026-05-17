"""Eval metric — Hit@k.

Checks if relevant items appear in the top-k predictions.

Usage:
    from naijareview.eval.metrics.hit_at_k import compute_hit_at_k

    hit = compute_hit_at_k(predicted_ids, [true_id], k=5)
    hit = compute_hit_at_k(predicted_ids, true_id, k=10)  # single ID also works
"""

from __future__ import annotations

from typing import Union


def compute_hit_at_k(
    predicted_item_ids: list[str],
    true_item_ids: Union[str, list[str]],
    k: int = 10,
) -> bool:
    """Check if any relevant item appears in the top-k predictions.

    Args:
        predicted_item_ids: Ranked list of recommended item IDs.
        true_item_ids: A single relevant item ID or a list of relevant IDs.
        k: Cutoff rank (default 10).

    Returns:
        True if at least one relevant item is in the top-k.
    """
    if isinstance(true_item_ids, str):
        true_item_ids = [true_item_ids]

    if not predicted_item_ids or not true_item_ids:
        return False

    top_k = set(predicted_item_ids[:k])
    return bool(top_k & set(true_item_ids))
