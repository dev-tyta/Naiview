"""User-related schemas: Review, UserHistory, Fingerprint, RegionProfile."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Review(BaseModel):
    """A single user review."""

    review_id: str
    user_id: str
    item_id: str
    text: str
    stars: float = Field(ge=1.0, le=5.0)
    timestamp: datetime
    item_category: str


class UserHistory(BaseModel):
    """Aggregated review history for a single user."""

    user_id: str
    reviews: list[Review]
    review_count: int
    earliest_review: datetime | None = None
    latest_review: datetime | None = None

    @property
    def has_sufficient_history(self) -> bool:
        """True if the user has enough reviews for reliable fingerprinting."""
        return self.review_count >= 3


class Fingerprint(BaseModel):
    """7-dimensional behavioural fingerprint derived from a user's review history."""

    user_id: str
    generosity_score: float = Field(ge=0.0, le=1.0)
    verbosity_score: float = Field(ge=0.0, le=1.0)
    verbosity_word_range: tuple[int, int]
    emotional_intensity: float = Field(ge=0.0, le=1.0)
    emotional_style: Literal["calm", "balanced", "passionate", "dramatic"]
    topic_focus: list[str]  # e.g. ["food", "service", "value"]
    consistency_score: float = Field(ge=0.0, le=1.0)
    recency_weight: float = Field(ge=0.0, le=1.0)
    naija_slang_index: float = Field(ge=0.0, le=1.0)
    confidence_intervals: dict[str, tuple[float, float]]
    computed_at: datetime
    review_count_at_computation: int


class RegionProfile(BaseModel):
    """Inferred Nigerian region for a user, with confidence and source signals."""

    user_id: str
    region: Literal["Lagos", "Abuja", "Port Harcourt", "Kano", "Enugu", "Unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    signals: list[str]  # Which phrases / mentions triggered the inference
