"""Eval metric stubs — Hit@k."""

from __future__ import annotations


def compute_hit_at_k(predicted_item_ids: list[str], true_item_id: str, k: int = 10) -> bool:
    """Check if the true item appears in the top-k predictions."""
    return true_item_id in predicted_item_ids[:k]
