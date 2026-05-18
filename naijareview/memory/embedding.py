"""Shared embedding provider — lazy-loaded SentenceTransformer.

Supports both MiniLM (384d, fast) and BGE-M3 (1024d, better multilingual).
Model is selected from config.embedding_model, defaulting to MiniLM.

Usage:
    from naijareview.memory.embedding import EmbeddingProvider

    # Uses config model (default: MiniLM for backward compat)
    provider = EmbeddingProvider()
    vec  = provider.embed("single string")
    vecs = provider.embed_batch(["one", "two"])
    dim  = provider.dim()

    # Explicit model
    bge = EmbeddingProvider("BAAI/bge-m3")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BGE_M3_MODEL  = "BAAI/bge-m3"

_DIM_MAP: dict[str, int] = {
    MINILM_MODEL:              384,
    BGE_M3_MODEL:              1024,
    "BAAI/bge-large-en-v1.5": 1024,
    "BAAI/bge-base-en-v1.5":   768,
    "BAAI/bge-small-en-v1.5":  384,
}


def _config_model() -> str:
    """Read embedding_model from settings, fall back to MiniLM."""
    try:
        from naijareview.config import settings
        return settings.embedding_model
    except Exception:
        return MINILM_MODEL


class EmbeddingProvider:
    """Lazy-loaded embedding provider — one instance per model name.

    Instances are cached by model name so the same model is never loaded twice
    in the same process.
    """

    _cache: dict[str, Any] = {}

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or _config_model()

    # ── Public API ───────────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """Embed a single string. Vector length == self.dim()."""
        return self.embed_batch([text])[0]

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """Embed a list of strings.

        Returns a list of float vectors (length == self.dim()).
        """
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
        )
        return [vec.tolist() for vec in embeddings]

    def dim(self) -> int:
        """Return the embedding dimension for this model."""
        return _DIM_MAP.get(self.model_name, self._get_model().get_sentence_embedding_dimension())

    # ── Lazy init ────────────────────────────────────────────────────────

    def _get_model(self) -> Any:
        if self.model_name not in EmbeddingProvider._cache:
            logger.info("Loading embedding model: %s", self.model_name)
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.model_name)
            EmbeddingProvider._cache[self.model_name] = model
            logger.info("Model loaded (dim=%d)", model.get_sentence_embedding_dimension())
        return EmbeddingProvider._cache[self.model_name]
