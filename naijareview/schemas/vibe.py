"""Vibe scoring schemas: VibeScore, AbegBreakdown."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class VibeScore(BaseModel):
    """Cultural authenticity score — computed on every output.

    Abeg formula: 0.4 × cultural_authenticity + 0.35 × cultural_accuracy
                  + 0.25 × persona_consistency

    When naija_vibe_mode=False, scored_in_mode='passive' and the score
    is informational only (graph never routes to regeneration).
    When naija_vibe_mode=True, scored_in_mode='active' and scores below
    vibe_regen_threshold trigger regeneration (up to vibe_max_retries).
    """

    cultural_authenticity: float = Field(ge=0.0, le=1.0)
    cultural_accuracy: float = Field(ge=0.0, le=1.0)
    persona_consistency: float = Field(ge=0.0, le=1.0)
    abeg_score: float = Field(ge=0.0, le=1.0)
    breakdown: dict[str, str] = Field(default_factory=dict)
    scored_in_mode: Literal["passive", "active"] = "passive"


class AbegBreakdown(BaseModel):
    """Detailed breakdown of the Abeg score for UI display."""

    cultural_authenticity_detail: str = ""
    cultural_accuracy_detail: str = ""
    persona_consistency_detail: str = ""
    improvement_suggestions: list[str] = Field(default_factory=list)
