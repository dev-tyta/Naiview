"""Item-related schemas: Item, RankedItem, Candidate, Recommendation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Item(BaseModel):
    """A reviewable item (restaurant, product, etc.)."""

    item_id: str
    name: str
    category: str
    nigerian_category: str | None = None  # From taxonomy overlay
    attributes: dict[str, str] = Field(default_factory=dict)
    avg_rating: float = 0.0
    review_count: int = 0
    description: str | None = None


class RankedItem(BaseModel):
    """An item with its rank and alignment score from the reranking step."""

    item: Item
    rank: int
    alignment_score: float = Field(ge=0.0, le=1.0)
    reasoning_snippet: str  # Why this item ranks here


class Candidate(BaseModel):
    """A retrieval candidate before reranking — carries raw scores."""

    item: Item
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    combined_score: float = 0.0


class Recommendation(BaseModel):
    """A final recommendation shown to the user."""

    item: Item
    rank: int
    explanation: str  # Nigerian-register reasoning shown to user
    alignment_dimensions: list[str]  # Which fingerprint dims it matches
