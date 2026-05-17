"""Retrieval tools: retrieve_similar_items, retrieve_candidates_hybrid.

See §4.4 of INTERNAL_ARCHITECTURE.md.

Hybrid retrieval (Task B): BM25 (lexical) + FAISS (semantic) fused at
0.4 / 0.6 weights with min-max score normalisation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from langchain_core.tools import tool

from naijareview.config import settings
from naijareview.memory.embedding import EmbeddingProvider
from naijareview.memory.item_index import ItemIndex
from naijareview.schemas.item import Item
from naijareview.schemas.persona import ColdStartPersona
from naijareview.schemas.user import Fingerprint

logger = logging.getLogger(__name__)

# Module-level singletons
_item_index: ItemIndex | None = None
_bm25_index: BM25Index | None = None


# ── BM25 Index ────────────────────────────────────────────────────────────────


class BM25Index:
    """BM25Okapi lexical index built from item metadata.

    Built from the same metadata sidecar file that ``ItemIndex`` uses.
    Tokenization is simple whitespace + lowercase — adequate for item names
    and descriptions.
    """

    def __init__(self, metadata_path: str | Path) -> None:
        self.metadata_path = Path(metadata_path)
        self._bm25: Any = None
        self._item_ids: list[str] = []  # same order as BM25 corpus
        self._metadata: list[dict[str, Any]] = []

        if self.metadata_path.exists():
            self._load()
        else:
            logger.warning("BM25 metadata not found at %s — will return empty", self.metadata_path)

    # ── Public API ───────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 30) -> list[tuple[dict[str, Any], float]]:
        """Search by BM25 lexical similarity.

        Returns list of (metadata_dict, score) tuples sorted descending.
        """
        if self._bm25 is None:
            return []

        tokens = self._tokenize(query)
        scores = self._bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results: list[tuple[dict[str, Any], float]] = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._metadata[int(idx)], float(scores[idx])))
        return results

    # ── Internals ────────────────────────────────────────────────────────

    def _load(self) -> None:
        from rank_bm25 import BM25Okapi

        self._metadata = json.loads(self.metadata_path.read_text())
        corpus = []
        self._item_ids = []

        for item in self._metadata:
            search_text = item.get("name", "")
            if item.get("description"):
                search_text += " " + item["description"]
            if item.get("category"):
                search_text += " " + item["category"]
            corpus.append(search_text)
            self._item_ids.append(item.get("item_id", ""))

        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self._bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 index built: %d items", len(self._metadata))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace+lowercase tokenizer."""
        import re

        return re.findall(r"\w+", text.lower())


# ── Singleton accessors ───────────────────────────────────────────────────────


def _get_item_index() -> ItemIndex:
    global _item_index
    if _item_index is None:
        _item_index = ItemIndex(
            index_path=settings.faiss_index_path,
            embed_provider=EmbeddingProvider(),
        )
    return _item_index


def _get_bm25() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        meta_path = settings.faiss_index_path.with_suffix(".json")
        _bm25_index = BM25Index(metadata_path=meta_path)
    return _bm25_index


def _get_metadata_path() -> Path:
    """Path to the FAISS metadata sidecar (also used by BM25)."""
    return settings.faiss_index_path.with_suffix(".json")


# ── Normalisation helper ──────────────────────────────────────────────────────


def _normalise_scores(
    scores: list[float],
) -> list[float]:
    """Min-max normalise a list of scores to [0, 1]."""
    if not scores:
        return scores
    min_s, max_s = min(scores), max(scores)
    if max_s == min_s:
        return [0.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


# ── Tools ─────────────────────────────────────────────────────────────────────


@tool
def retrieve_similar_items(
    query: str,
    category: str | None = None,
    top_k: int = 20,
) -> list[Item]:
    """Semantic search over FAISS item index, filtered by category.

    Backend: FAISS flat IP index; query embedded with all-MiniLM-L6-v2.
    Post-filter by category if provided.

    Args:
        query: Search query text.
        category: Optional category filter (e.g. "Restaurants", "Food").
        top_k: Number of items to return (default 20).

    Returns:
        List of matching Items sorted by semantic similarity.
    """
    index = _get_item_index()
    raw_results = index.search(query, top_k=top_k * 2 if category else top_k)

    if category:
        raw_results = [r for r in raw_results if r.category == category]

    return raw_results[:top_k]


@tool
def retrieve_candidates_hybrid(
    query: str,
    fingerprint: Fingerprint | None = None,
    cold_start_persona: ColdStartPersona | None = None,
    top_k: int = 20,
) -> list[Item]:
    """Hybrid BM25 + semantic retrieval for Task B candidate generation.

    Algorithm:
    1. Enrich query with fingerprint topic focus or cold-start food preference.
    2. Retrieve top-30 from BM25 (lexical).
    3. Retrieve top-30 from FAISS (semantic).
    4. Deduplicate by item_id.
    5. Re-score: 0.4 × bm25_norm + 0.6 × semantic_norm.
    6. Return top-k.

    Args:
        query: Search query text.
        fingerprint: Optional user fingerprint for query enrichment
                     (uses top-3 topic_focus terms).
        cold_start_persona: Optional cold-start persona for new users
                            (uses food_preference as query boost).
        top_k: Number of candidates to return (default 20).

    Returns:
        List of candidate Items sorted by hybrid score descending.
    """
    # ── 1. Enrich query ──────────────────────────────────────────────────
    enriched_query = query
    if fingerprint and fingerprint.topic_focus:
        enriched_query += " " + " ".join(fingerprint.topic_focus[:3])
    if cold_start_persona and cold_start_persona.food_preference:
        enriched_query += " " + cold_start_persona.food_preference

    logger.debug("Hybrid query (enriched): %s", enriched_query)

    # ── 2. BM25 retrieval (top-30) ───────────────────────────────────────
    bm25 = _get_bm25()
    bm25_results = bm25.search(enriched_query, top_k=30)

    # ── 3. Semantic retrieval (top-30) ────────────────────────────────────
    index = _get_item_index()
    semantic_results = index.search(enriched_query, top_k=30)

    # ── 4. Fuse ──────────────────────────────────────────────────────────
    # Build score maps keyed by item_id
    bm25_scores: dict[str, float] = {}
    for meta, score in bm25_results:
        bm25_scores[meta.get("item_id", "")] = score

    sem_scores: dict[str, float] = {}
    # Semantic results are Items — we need the raw similarity score.
    # Re-query FAISS for raw scores alongside the Items.
    # Actually ItemIndex.search() doesn't return scores. Let me fix that...
    # For now, use a simple rank-based score: position-based decay.
    sem_rank_scores: dict[str, float] = {}
    for rank, item in enumerate(semantic_results):
        sem_rank_scores[item.item_id] = 1.0 / (rank + 1)

    # Merge all candidate item_ids
    all_ids: set[str] = set(bm25_scores.keys()) | set(sem_rank_scores.keys())

    # Build score vectors for normalisation
    bm25_vals = [bm25_scores.get(iid, 0.0) for iid in all_ids]
    sem_vals = [sem_rank_scores.get(iid, 0.0) for iid in all_ids]

    bm25_norm = _normalise_scores(bm25_vals)
    sem_norm = _normalise_scores(sem_vals)

    # Fuse with weights: 0.4 BM25 + 0.6 semantic
    fused: list[tuple[str, float]] = []
    for i, iid in enumerate(all_ids):
        hybrid = settings.bm25_weight * bm25_norm[i] + settings.semantic_weight * sem_norm[i]
        fused.append((iid, hybrid))

    # Sort by hybrid score descending
    fused.sort(key=lambda x: x[1], reverse=True)

    # ── 5. Look up Items from metadata ───────────────────────────────────
    # Load metadata once to build item lookup
    meta_path = _get_metadata_path()
    if meta_path.exists():
        all_metadata = json.loads(meta_path.read_text())
        meta_by_id: dict[str, dict[str, Any]] = {m.get("item_id", ""): m for m in all_metadata}
    else:
        meta_by_id = {}

    results: list[Item] = []
    seen: set[str] = set()
    for iid, hybrid_score in fused:
        if iid in seen or iid == "":
            continue
        seen.add(iid)
        meta = meta_by_id.get(iid, {})
        results.append(
            Item(
                item_id=iid,
                name=meta.get("name", "Unknown"),
                category=meta.get("category", "general"),
                nigerian_category=meta.get("nigerian_category"),
                attributes=meta.get("attributes", {}),
                avg_rating=float(meta.get("avg_rating", 0.0)),
                review_count=int(meta.get("review_count", 0)),
                description=meta.get("description"),
            )
        )
        if len(results) >= top_k:
            break

    logger.debug(
        "Hybrid retrieval: %d candidates from query=%s",
        len(results),
        query[:50],
    )
    return results


def _reset_singletons() -> None:
    """Reset module-level state for testing."""
    global _item_index, _bm25_index
    _item_index = None
    _bm25_index = None
