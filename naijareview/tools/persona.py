"""Persona tools: fetch_few_shot_examples, cold_start_interview.

See §4.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

from naijareview.schemas.persona import ColdStartPersona


@tool
def fetch_few_shot_examples(
    region: str,
    sentiment: Literal["positive", "negative", "mixed"],
    category: str,
    k: int = 3,
) -> list[str]:
    """Retrieve authentic Nigerian review examples matching region, sentiment, category.

    Backend: Pre-indexed AfriSenti + NaijaSenti + synthetic corpus,
    partitioned by (region, sentiment, category).
    Falls back to (region, sentiment, *) if exact category has too few samples.

    Args:
        region: Nigerian region to match.
        sentiment: Target sentiment.
        category: Item category.
        k: Number of examples to retrieve (default 3).

    Returns:
        List of example review strings.
    """
    # TODO: Implement — Shiloh owns phrase library
    raise NotImplementedError("fetch_few_shot_examples not yet implemented")


@tool
def cold_start_interview(
    turn_history: list[dict],
) -> tuple[str, ColdStartPersona | None]:
    """Run one turn of the cold-start onboarding conversation.

    Turn 1: Ask food preference → parse → store food_preference
    Turn 2: Ask value orientation → parse → store value_orientation
    Turn 3: Ask atmosphere + budget → parse → store both
    After turn 3: set frequency_of_dining_out = "occasional", return persona

    Args:
        turn_history: List of {role, content} dicts from conversation so far.

    Returns:
        Tuple of (agent's next utterance, completed persona or None).
    """
    # TODO: Implement — Aaliyah owns ColdStartBootstrapper skill
    raise NotImplementedError("cold_start_interview not yet implemented")
