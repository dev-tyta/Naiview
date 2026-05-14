"""Item Index — FAISS wrapper for the global item embedding index.

Owner: Aaliyah
See §3.1 of INTERNAL_ARCHITECTURE.md.

FAISS flat IP index + metadata sidecar.
Built once at data-prep, rebuilt on dataset refresh.
"""

from __future__ import annotations


class ItemIndex:
    """FAISS-backed index for semantic item retrieval."""

    def __init__(self, index_path: str, embedding_model: str) -> None:
        self.index_path = index_path
        self.embedding_model = embedding_model
        # TODO: Load FAISS index and metadata sidecar

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[dict]:
        """Search for items similar to the query embedding."""
        # TODO: Implement
        raise NotImplementedError

    def build_index(self, items: list[dict]) -> None:
        """Build the FAISS index from a list of items."""
        # TODO: Implement
        raise NotImplementedError
