"""Output schemas: ReviewOutput (Task A), RecommendationOutput (Task B)."""

from __future__ import annotations

from pydantic import BaseModel

from naijareview.schemas.item import Recommendation


class ReviewOutput(BaseModel):
    """Complete output payload for a Task A review generation request."""

    generated_review: str
    predicted_rating: float
    confidence: float
    fingerprint_match: str  # Human-readable summary
    style_notes: str
    abeg_score: float | None = None  # Always populated (passive or active)
    vibe_breakdown: dict[str, float] | None = None
    naija_vibe_mode_active: bool = False
    retry_count: int = 0


class RecommendationOutput(BaseModel):
    """Complete output payload for a Task B recommendation request."""

    recommendations: list[Recommendation]
    reasoning: str | None = None
    confidence: float | None = None
    cold_start_mode: bool = False
    diversity_score: float = 0.0
    follow_up_question: str | None = None
    naija_vibe_mode_active: bool = False
