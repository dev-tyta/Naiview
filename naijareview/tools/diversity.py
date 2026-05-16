"""Diversity tools: diversity_check.

See §4.7 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from collections import Counter

from langchain_core.tools import tool

from naijareview.schemas.item import RankedItem


def _compute_diversity(ranked_items: list[RankedItem]) -> float:
    """Compute diversity = 1 - (max_category_count / total_count)."""
    if not ranked_items:
        return 1.0
    counts = Counter(ri.item.category for ri in ranked_items)
    max_count = max(counts.values())
    return 1.0 - (max_count / len(ranked_items))


@tool
def diversity_check(
    ranked_items: list[RankedItem],
    min_diversity: float = 0.6,
) -> tuple[list[RankedItem], float]:
    """Ensure recommended set isn't dominated by one category.

    Algorithm:
    1. Compute diversity = 1 − (max category count / total count).
    2. If diversity < min_diversity, swap lowest-ranked item from dominant
       category with highest-ranked item from a different category below top-5.
    3. Repeat until diversity ≥ min_diversity or no swaps possible.

    Args:
        ranked_items: The current ranked item list.
        min_diversity: Minimum acceptable diversity score (default 0.6).

    Returns:
        Tuple of (possibly-reordered list, diversity score).
    """
    if not ranked_items:
        return (ranked_items, 1.0)

    items = list(ranked_items)
    max_swaps = 3

    for _ in range(max_swaps):
        diversity = _compute_diversity(items)
        if diversity >= min_diversity:
            break

        # Find dominant category
        counts = Counter(ri.item.category for ri in items)
        dominant_cat = max(counts, key=lambda c: counts[c])

        # Find the lowest-ranked item from the dominant category
        # (highest rank number = worst position in the list)
        dominant_items_indices = [
            i for i, ri in enumerate(items) if ri.item.category == dominant_cat
        ]
        if not dominant_items_indices:
            break

        # "Lowest ranked" = the one with the highest rank number among dominant cat
        swap_out_idx = max(dominant_items_indices, key=lambda i: items[i].rank)

        # Find the highest-ranked item NOT in dominant category that's below position 5
        # (i.e., list index >= 5, which means rank > 5)
        candidates_for_swap_in = [
            i for i, ri in enumerate(items)
            if ri.item.category != dominant_cat and i >= 5
        ]

        if not candidates_for_swap_in:
            # Try any non-dominant item below the swap_out position
            candidates_for_swap_in = [
                i for i, ri in enumerate(items)
                if ri.item.category != dominant_cat and i > swap_out_idx
            ]
            if not candidates_for_swap_in:
                break

        # Highest-ranked means lowest list index (best position)
        swap_in_idx = min(candidates_for_swap_in)

        # Perform the swap in the list
        items[swap_out_idx], items[swap_in_idx] = items[swap_in_idx], items[swap_out_idx]

        # Re-assign rank numbers to reflect new positions
        for pos, ri in enumerate(items):
            items[pos] = RankedItem(
                item=ri.item,
                rank=pos + 1,
                alignment_score=ri.alignment_score,
                reasoning_snippet=ri.reasoning_snippet,
            )

    final_diversity = _compute_diversity(items)
    return (items, final_diversity)
