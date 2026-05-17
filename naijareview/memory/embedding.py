"""Shared embedding provider — lazy-loaded SentenceTransformer singleton.

Both ChromaDB (episodic memory) and FAISS (item index) use the same
embedding model: ``sentence-transformers/all-MiniLM-L6-v2`` (384-dim).

Usage:
    from naijareview.memory.embedding import EmbeddingProvider

    provider = EmbeddingProvider()
    vec  = provider.embed("single string")
    vecs = provider.embed_batch(["one", "two", "three"])
    dim  = provider.dim()  # 384
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384


class EmbeddingProvider:
    """Lazy-loaded singleton embedding provider.

    The SentenceTransformer model is loaded on first call (∼200ms cold start)
    and cached for the lifetime of the process.
    """

    _model: Any = None  # SentenceTransformer instance

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self.model_name = model_name

    # ── Public API ───────────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns a 384-dim float vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings. Returns list of 384-dim float vectors."""
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        # embeddings is a numpy array — convert to list of lists
        return [vec.tolist() for vec in embeddings]

    @staticmethod
    def dim() -> int:
        """Return the embedding dimension (384)."""
        return _EMBEDDING_DIM

    # ── Lazy init ───────────────────────────────────────────────────────

    def _get_model(self) -> Any:
        if EmbeddingProvider._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            # Delayed import — sentence-transformers is heavy and in the ml group
            from sentence_transformers import SentenceTransformer

            EmbeddingProvider._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded (dim=%d)", _EMBEDDING_DIM)
        return EmbeddingProvider._model
