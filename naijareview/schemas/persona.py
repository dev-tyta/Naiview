"""Persona schemas: ColdStartPersona, NigerianPersona."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ColdStartPersona(BaseModel):
    """Persona built from the 3-turn cold-start onboarding interview."""

    user_id: str  # Anonymous ID for new users
    food_preference: str | None = None
    value_orientation: Literal["taste_first", "value_first", "balanced"] | None = None
    atmosphere_preference: Literal["lively", "quiet", "either"] | None = None
    budget_range: Literal["low", "mid", "high"] | None = None
    frequency_of_dining_out: Literal["rare", "occasional", "frequent"] | None = None
    turns_completed: int = 0


class NigerianPersona(BaseModel):
    """Extended persona with Nigerian-specific cultural context.

    Used when the PersonaAuthor skill builds the persona prompt block
    for the generation LLM.
    """

    base_persona: ColdStartPersona | None = None
    region: str = "Unknown"
    pidgin_comfort: float = 0.0  # 0 = formal English, 1 = heavy Pidgin
    cultural_markers: list[str] = []  # Regional food/place references
    intensity: Literal["natural", "amplified"] = "natural"
