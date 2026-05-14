"""Yelp → Nigerian category taxonomy mapping.

Owner: Shiloh
See §4.7 apply_nigerian_taxonomy.
Backend: data/taxonomy.yaml
"""

from __future__ import annotations

from pathlib import Path

import yaml


class TaxonomyMapper:
    """Map Yelp/Amazon categories to Nigerian equivalents."""

    def __init__(self, taxonomy_path: str = "data/taxonomy.yaml") -> None:
        self.taxonomy_path = Path(taxonomy_path)
        self._mapping: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load taxonomy mapping from YAML."""
        if self.taxonomy_path.exists():
            with open(self.taxonomy_path) as f:
                self._mapping = yaml.safe_load(f) or {}

    def map_category(self, category: str) -> str:
        """Map a category to its Nigerian equivalent. Falls back to original."""
        return self._mapping.get(category, category)
