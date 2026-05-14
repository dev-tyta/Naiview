"""Taxonomy tools: apply_nigerian_taxonomy.

See §4.7 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.item import Item


@tool
def apply_nigerian_taxonomy(item: Item) -> Item:
    """Remap an item's Yelp/Amazon category to its Nigerian equivalent.

    Backend: YAML-loaded mapping in data/taxonomy.yaml.
    Falls back to original category if no mapping exists.

    Args:
        item: The item to remap.

    Returns:
        Item with nigerian_category field filled in.
    """
    # TODO: Implement — Shiloh owns taxonomy YAML
    raise NotImplementedError("apply_nigerian_taxonomy not yet implemented")
