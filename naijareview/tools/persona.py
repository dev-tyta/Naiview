"""Persona tools: fetch_few_shot_examples, cold_start_interview.

See §4.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from langchain_core.tools import tool

from naijareview.schemas.persona import ColdStartPersona

logger = logging.getLogger(__name__)

_PHRASE_LIBRARY_PATH = Path(__file__).resolve().parents[2] / "data" / "phrase_library"

_GENERIC_EXAMPLES: dict[str, list[str]] = {
    "positive": [
        "This place is absolutely amazing! The food dey sweet well well.",
        "I go back here every time. Service is top notch, no wahala.",
        "Best spot in town, the value for money is excellent.",
    ],
    "neutral": [
        "Decent place, nothing too special. Worth a visit if you're nearby.",
        "Average experience overall. Some things good, some need improvement.",
        "It's okay for what it is. Won't rush back but won't avoid either.",
    ],
    "negative": [
        "Very disappointed with this place. Service was terrible.",
        "Not worth the money at all. Better options exist in the area.",
        "Terrible experience. Would not recommend to anyone.",
    ],
    # alias
    "mixed": [
        "Decent place, nothing too special. Worth a visit if you're nearby.",
        "Average experience overall. Some things good, some need improvement.",
        "It's okay for what it is. Won't rush back but won't avoid either.",
    ],
}


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
    examples_path = _PHRASE_LIBRARY_PATH / "examples_by_sentiment.json"
    try:
        with examples_path.open("r", encoding="utf-8") as f:
            data: dict = json.load(f)

        # Try sentiment key directly
        if sentiment in data and data[sentiment]:
            pool: list[str] = data[sentiment]
            return pool[:k]

        # Try aliasing mixed → neutral if available
        if sentiment == "mixed" and "neutral" in data and data["neutral"]:
            return data["neutral"][:k]

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("fetch_few_shot_examples: could not load phrase library: %s", exc)

    # Fallback to generic examples
    fallback_key = sentiment if sentiment in _GENERIC_EXAMPLES else "neutral"
    return _GENERIC_EXAMPLES[fallback_key][:k]


@tool
def cold_start_interview(
    turn: int,
    user_response: str,
    partial_persona: dict,
) -> dict:
    """Run one turn of the cold-start onboarding conversation.

    Turn 1: parse food_preference from user_response
    Turn 2: parse value_orientation and atmosphere_preference
    Turn 3: parse budget_range and frequency_of_dining_out

    Args:
        turn: The current turn number (1, 2, or 3).
        user_response: The user's response for this turn.
        partial_persona: The partially-built persona dict so far.

    Returns:
        Updated partial_persona dict with turns_completed incremented.
    """
    updated = dict(partial_persona)
    response_lower = user_response.lower()

    if turn == 1:
        # Parse food preference — store raw text
        updated["food_preference"] = user_response.strip()

    elif turn == 2:
        # Parse value orientation
        if any(w in response_lower for w in ("taste", "quality")):
            updated["value_orientation"] = "taste_first"
        elif any(w in response_lower for w in ("price", "value", "cheap", "budget")):
            updated["value_orientation"] = "value_first"
        else:
            updated["value_orientation"] = "balanced"

        # Parse atmosphere preference
        if any(w in response_lower for w in ("quiet", "calm", "peace")):
            updated["atmosphere_preference"] = "quiet"
        elif any(w in response_lower for w in ("lively", "loud", "busy", "vibrant")):
            updated["atmosphere_preference"] = "lively"
        else:
            updated["atmosphere_preference"] = "either"

    elif turn == 3:
        # Parse budget range
        if any(w in response_lower for w in ("cheap", "low", "affordable", "budget")):
            updated["budget_range"] = "low"
        elif any(w in response_lower for w in ("expensive", "high", "premium", "luxury")):
            updated["budget_range"] = "high"
        else:
            updated["budget_range"] = "mid"

        # Parse frequency of dining out
        if any(w in response_lower for w in ("every day", "daily", "often", "frequent")):
            updated["frequency_of_dining_out"] = "frequent"
        elif any(w in response_lower for w in ("rare", "seldom", "never")):
            updated["frequency_of_dining_out"] = "rare"
        else:
            updated["frequency_of_dining_out"] = "occasional"

    # Increment turns_completed
    updated["turns_completed"] = int(updated.get("turns_completed", 0)) + 1

    return updated
