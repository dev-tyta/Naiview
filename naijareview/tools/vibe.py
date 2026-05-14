"""Vibe tools: run_naija_vibe_check, score_abeg_batch.

See §4.6 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

from naijareview.schemas.item import Item
from naijareview.schemas.user import Fingerprint
from naijareview.schemas.vibe import VibeScore


@tool
def run_naija_vibe_check(
    review_text: str,
    target_fingerprint: Fingerprint,
    item: Item,
    mode: Literal["passive", "active"],
) -> VibeScore:
    """Score a generated review on Nigerian authenticity, cultural accuracy, persona consistency.

    Always runs; behaviour at threshold depends on mode.
    The tool does NOT decide to retry — the graph's conditional edge reads
    mode and abeg_score and decides whether to route to regeneration.

    Algorithm:
    - Nigerian authenticity: weighted (slang-token fraction) + (LLM-judged Haiku score)
    - Cultural accuracy: LLM-judged (Haiku) — correct regional context, food names, slang
    - Persona consistency: cosine(fingerprint embedding, review embedding), mapped [0,1]
    - Abeg score: 0.4 × authenticity + 0.35 × cultural + 0.25 × persona

    Args:
        review_text: The generated review to score.
        target_fingerprint: The user's behavioural fingerprint.
        item: The item being reviewed.
        mode: "passive" or "active" (affects scored_in_mode field only).

    Returns:
        VibeScore with all sub-scores and the composite abeg_score.
    """
    # TODO: Implement — Testimony owns NaijaVibeChecker skill
    raise NotImplementedError("run_naija_vibe_check not yet implemented")


@tool
def score_abeg_batch(
    reviews: list[str],
    fingerprints: list[Fingerprint],
    items: list[Item],
) -> list[VibeScore]:
    """Run vibe check across a batch (for eval harness and synthetic corpus filtering).

    Always runs in passive mode.

    Args:
        reviews: List of review texts to score.
        fingerprints: Corresponding fingerprints.
        items: Corresponding items.

    Returns:
        List of VibeScores, one per input.
    """
    # TODO: Implement — batch wrapper around run_naija_vibe_check
    raise NotImplementedError("score_abeg_batch not yet implemented")
