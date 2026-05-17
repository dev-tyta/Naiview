"""Item Index — FAISS wrapper for the global item embedding index.

Owner: Aaliyah
See §3.1 of INTERNAL_ARCHITECTURE.md.

FAISS flat IP index + metadata sidecar.
Built once at data-prep (``build_index``), rebuilt on dataset refresh.
Loaded at startup (``search``) for inference-time retrieval.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim).
Search returns cosine-similarity scores (inner product on unit-normalised vectors).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from naijareview.memory.embedding import EmbeddingProvider
from naijareview.schemas.item import Item

logger = logging.getLogger(__name__)


class ItemIndex:
    """FAISS-backed index for semantic item retrieval.

    Usage:
        index = ItemIndex(index_path="./data/faiss/index", metadata_path="./data/faiss/metadata.json")
        results = index.search("Nigerian suya joint", top_k=5)
        # → [Item(...), Item(...), ...]
    """

    def __init__(
        self,
        index_path: str | Path,
        metadata_path: str | Path = "",
        embed_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.index_path = Path(index_path)
        self.metadata_path = (
            Path(metadata_path) if metadata_path else self.index_path.with_suffix(".json")
        )
        self._embed_provider = embed_provider or EmbeddingProvider()
        self._index: Any = None  # faiss.Index
        self._metadata: list[dict[str, Any]] = []  # parallel list, same order as index

    # ── Public API ───────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 20) -> list[Item]:
        """Search for items similar to the query text.

        Args:
            query: Natural language search query.
            top_k: Number of items to return.

        Returns:
            List of Items sorted by descending similarity score.
        """
        index, metadata = self._ensure_loaded()

        if index.ntotal == 0:
            logger.warning("FAISS index is empty — no items to search")
            return []

        query_vec = np.array([self._embed_provider.embed(query)], dtype=np.float32)
        scores, indices = index.search(query_vec, top_k)

        results: list[Item] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue  # FAISS returns -1 when there aren't enough results
            meta = metadata[int(idx)]
            results.append(
                Item(
                    item_id=meta.get("item_id", str(idx)),
                    name=meta.get("name", "Unknown"),
                    category=meta.get("category", "general"),
                    nigerian_category=meta.get("nigerian_category"),
                    attributes=meta.get("attributes", {}),
                    avg_rating=float(meta.get("avg_rating", 0.0)),
                    review_count=int(meta.get("review_count", 0)),
                    description=meta.get("description"),
                )
            )

        return results

    def build_index(self, items: list[dict[str, Any]]) -> None:
        """Build the FAISS index from a list of item dicts.

        Each item dict must have at minimum an ``item_id`` and ``name``.
        Other fields (``category``, ``description``, ``avg_rating``, etc.)
        are preserved in the metadata sidecar.

        The index is written to ``self.index_path`` and metadata to
        ``self.metadata_path``.
        """
        import faiss

        texts = []
        metadata: list[dict[str, Any]] = []

        for item in items:
            # Build a searchable text from available fields
            search_text = item.get("name", "")
            if item.get("description"):
                search_text += " " + item["description"]
            if item.get("category"):
                search_text += " " + item["category"]
            texts.append(search_text)
            metadata.append(item)

        logger.info("Embedding %d items for FAISS index...", len(texts))
        embeddings = self._embed_provider.embed_batch(texts)
        embedding_matrix = np.array(embeddings, dtype=np.float32)

        dim = embedding_matrix.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embedding_matrix)

        # Persist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(metadata, indent=2, default=str))

        self._index = index
        self._metadata = metadata
        logger.info(
            "FAISS index built: %d items, dim=%d → %s",
            len(metadata),
            dim,
            self.index_path,
        )

    # ── Internals ────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> tuple[Any, list[dict[str, Any]]]:
        """Lazy-load index and metadata from disk."""
        if self._index is not None and self._metadata:
            return self._index, self._metadata
        return self._load()

    def _load(self) -> tuple[Any, list[dict[str, Any]]]:
        """Load FAISS index and metadata from disk."""
        import faiss

        if not self.index_path.exists():
            logger.warning("FAISS index not found at %s — returning empty", self.index_path)
            self._index = faiss.IndexFlatIP(self._embed_provider.dim())
            self._metadata = []
            return self._index, self._metadata

        logger.info("Loading FAISS index from %s", self.index_path)
        self._index = faiss.read_index(str(self.index_path))

        if self.metadata_path.exists():
            self._metadata = json.loads(self.metadata_path.read_text())
            logger.info("Loaded metadata for %d items", len(self._metadata))
        else:
            logger.warning("Metadata not found at %s — returning empty results", self.metadata_path)
            self._metadata = []

        return self._index, self._metadata
