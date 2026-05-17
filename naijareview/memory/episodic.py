"""Episodic Memory — ChromaDB wrapper for user review history.

Owner: Aaliyah
See §10.1 of INTERNAL_ARCHITECTURE.md.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim).
Collection layout: single ``naijareview_reviews`` collection partitioned by
``user_id`` metadata filter (not one collection per user).

Read patterns:
- ``load_user_history`` — fetch all reviews for a user
- ``retrieve_similar`` — semantic search within a user's own reviews
Write patterns:
- ``add_review`` — append a new review
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from naijareview.memory.embedding import EmbeddingProvider
from naijareview.schemas.user import Review, UserHistory

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "naijareview_reviews"


class EpisodicMemory:
    """ChromaDB-backed episodic memory for user review histories.

    Uses a single collection with ``user_id`` stored in metadata for filtering.
    ChromaDB's built-in embedding function wraps the shared SentenceTransformer.
    """

    def __init__(
        self,
        persist_dir: str,
        collection_prefix: str = "naijareview",
        embed_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.persist_dir = persist_dir
        self.collection_name = f"{collection_prefix}_reviews"
        self._embed_provider = embed_provider or EmbeddingProvider()
        self._collection: Any = None  # lazily initialised

    # ── Public API ───────────────────────────────────────────────────────

    def load_user_history(self, user_id: str) -> UserHistory:
        """Fetch all reviews for a user from ChromaDB.

        Returns an empty ``UserHistory`` (with 0 reviews) if the user has no
        records — callers should check ``has_sufficient_history`` and route
        to cold-start flow if needed.
        """
        collection = self._get_collection()
        try:
            results = collection.get(
                where={"user_id": user_id},
                include=["documents", "metadatas", "embeddings"],
            )
        except Exception as exc:
            logger.warning("ChromaDB get failed for user %s: %s", user_id, exc)
            return UserHistory(user_id=user_id, reviews=[], review_count=0)

        reviews = self._parse_results(results)
        return UserHistory(
            user_id=user_id,
            reviews=reviews,
            review_count=len(reviews),
            earliest_review=min((r.timestamp for r in reviews), default=None),
            latest_review=max((r.timestamp for r in reviews), default=None),
        )

    def retrieve_similar(self, user_id: str, query: str, k: int = 5) -> list[Review]:
        """Semantic search within a user's review history.

        Returns the top-k most semantically similar reviews for this user.
        """
        collection = self._get_collection()
        query_embedding = self._embed_provider.embed(query)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"user_id": user_id},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.warning("ChromaDB query failed for user %s: %s", user_id, exc)
            return []

        return self._parse_query_results(results)

    def add_review(self, review: Review) -> None:
        """Persist a new review to episodic memory.

        Metadata schema:
        - user_id, item_id, stars (int), timestamp (ISO str), item_category
        """
        collection = self._get_collection()
        review_text = review.text or ""
        embedding = self._embed_provider.embed(review_text)

        # upsert instead of add — idempotent for generated reviews with stable IDs
        collection.upsert(
            embeddings=[embedding],
            documents=[review_text],
            metadatas=[
                {
                    "user_id": review.user_id,
                    "item_id": review.item_id,
                    "stars": float(review.stars),
                    "timestamp": review.timestamp.isoformat(),
                    "item_category": review.item_category,
                    "source": getattr(review, "source", "generated"),
                }
            ],
            ids=[review.review_id],
        )
        logger.debug("Review %s upserted to episodic memory (user=%s)", review.review_id, review.user_id)

    # ── Internals ────────────────────────────────────────────────────────

    def _get_collection(self) -> Any:
        """Lazy initialise ChromaDB client and collection."""
        if self._collection is not None:
            return self._collection

        import chromadb

        client = chromadb.PersistentClient(path=self.persist_dir)

        try:
            self._collection = client.get_collection(self.collection_name)
        except ValueError:
            # Collection doesn't exist yet — create it
            self._collection = client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        return self._collection

    def _parse_results(self, results: dict[str, Any]) -> list[Review]:
        """Parse ChromaDB ``get`` results into ``Review`` objects."""
        reviews: list[Review] = []
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            text = documents[idx] if idx < len(documents) else ""
            reviews.append(
                Review(
                    review_id=doc_id,
                    user_id=meta.get("user_id", ""),
                    item_id=meta.get("item_id", ""),
                    text=text,
                    stars=float(meta.get("stars", 0)),
                    timestamp=self._parse_ts(meta.get("timestamp", "")),
                    item_category=meta.get("item_category", ""),
                )
            )
        return reviews

    def _parse_query_results(self, results: dict[str, Any]) -> list[Review]:
        """Parse ChromaDB ``query`` results into ``Review`` objects."""
        reviews: list[Review] = []
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            text = documents[idx] if idx < len(documents) else ""
            reviews.append(
                Review(
                    review_id=doc_id,
                    user_id=meta.get("user_id", ""),
                    item_id=meta.get("item_id", ""),
                    text=text,
                    stars=float(meta.get("stars", 0)),
                    timestamp=self._parse_ts(meta.get("timestamp", "")),
                    item_category=meta.get("item_category", ""),
                )
            )
        return reviews

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.now()
