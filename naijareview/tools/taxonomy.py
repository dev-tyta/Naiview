"""Taxonomy tools: apply_nigerian_taxonomy.

See §4.7 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from langchain_core.tools import tool

from naijareview.schemas.item import Item

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_TAXONOMY_JSON = _DATA_DIR / "processed" / "taxonomy.json"
_TAXONOMY_YAML = _DATA_DIR / "taxonomy.yaml"


def _load_taxonomy_json() -> dict[str, str]:
    """Load taxonomy from data/processed/taxonomy.json.

    Returns a flat dict mapping category → nigerian_name.
    """
    with _TAXONOMY_JSON.open("r", encoding="utf-8") as f:
        data: dict = json.load(f)
    category_map: dict = data.get("category_map", {})
    # Flatten: {category: {nigerian_name: ..., ...}} → {category: nigerian_name}
    return {
        cat: info["nigerian_name"]
        for cat, info in category_map.items()
        if isinstance(info, dict) and "nigerian_name" in info
    }


def _load_taxonomy_yaml() -> dict[str, str]:
    """Load taxonomy from data/taxonomy.yaml (simple key: value pairs).

    The file uses Python-style comments (#) and the format:
        "Yelp Category": "Nigerian Equivalent"
    """
    mapping: dict[str, str] = {}
    with _TAXONOMY_YAML.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # Skip blank lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            # Match: "key": "value"
            match = re.match(r'^"([^"]+)"\s*:\s*"([^"]+)"', stripped)
            if match:
                mapping[match.group(1)] = match.group(2)
    return mapping


def _get_taxonomy() -> dict[str, str]:
    """Return the category mapping, preferring taxonomy.json over taxonomy.yaml."""
    try:
        return _load_taxonomy_json()
    except (FileNotFoundError, OSError, KeyError, json.JSONDecodeError) as exc:
        logger.debug("taxonomy.json unavailable (%s), falling back to YAML", exc)
    try:
        return _load_taxonomy_yaml()
    except (FileNotFoundError, OSError) as exc:
        logger.warning("taxonomy.yaml also unavailable: %s", exc)
    return {}


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
    try:
        taxonomy = _get_taxonomy()
        nigerian_name = taxonomy.get(item.category)

        if nigerian_name:
            return item.model_copy(update={"nigerian_category": nigerian_name})

        # Category not found — keep existing nigerian_category or fall back
        if item.nigerian_category:
            return item
        return item.model_copy(update={"nigerian_category": "General Restaurant"})

    except Exception as exc:
        logger.warning("apply_nigerian_taxonomy failed: %s", exc)
        # Return item unchanged on unexpected error
        if item.nigerian_category:
            return item
        return item.model_copy(update={"nigerian_category": "General Restaurant"})
