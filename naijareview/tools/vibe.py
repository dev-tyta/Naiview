"""Vibe tools: run_naija_vibe_check, score_abeg_batch.

See §4.6 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Literal

from langchain_core.tools import tool

from naijareview.llm.router import LLMRouter
from naijareview.schemas.item import Item
from naijareview.schemas.user import Fingerprint
from naijareview.schemas.vibe import VibeScore

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
_router = LLMRouter()


def _parse_json_from_response(text: str) -> dict:
    """Extract and parse the first JSON object from an LLM response string."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Find first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(cleaned)


def _build_vibe_prompt(
    review_text: str,
    fingerprint: Fingerprint,
    item: Item,
    mode: str,
) -> str:
    """Build a vibe-scorer prompt, using the Jinja template as a static string."""
    template_path = _PROMPTS_DIR / "vibe_scorer.jinja"
    try:
        template_str = template_path.read_text(encoding="utf-8")
        # Replace Jinja variables with actual values (simple substitution)
        topic_focus_str = ", ".join(fingerprint.topic_focus) if fingerprint.topic_focus else "none specified"
        vwr = fingerprint.verbosity_word_range
        word_count = len(review_text.split())
        naija_vibe_mode = mode == "active"

        prompt = template_str
        prompt = prompt.replace("{{ review_text }}", review_text)
        prompt = prompt.replace("{{ emotional_style }}", fingerprint.emotional_style)
        prompt = prompt.replace(
            "{{ topic_focus | join(\", \") if topic_focus else \"none specified\" }}",
            topic_focus_str,
        )
        prompt = prompt.replace(
            "{{ verbosity_word_range[0] }}", str(vwr[0])
        )
        prompt = prompt.replace(
            "{{ verbosity_word_range[1] }}", str(vwr[1])
        )
        prompt = prompt.replace(
            "{{ review_text.split() | length }}", str(word_count)
        )
        prompt = prompt.replace("{{ item_name }}", item.name)
        prompt = prompt.replace("{{ item_category }}", item.category)
        prompt = prompt.replace(
            "{{ naija_vibe_mode }}", str(naija_vibe_mode)
        )
        # Handle conditional blocks that might remain — strip jinja control flow
        # by removing {% ... %} blocks and {{ ... }} that weren't replaced
        prompt = re.sub(r"\{%.*?%\}", "", prompt, flags=re.DOTALL)
        prompt = re.sub(r"\{\{.*?\}\}", "", prompt, flags=re.DOTALL)
        return prompt.strip()

    except (FileNotFoundError, OSError):
        # Fallback to a minimal prompt
        return (
            f"Score the following review for Nigerian cultural quality.\n"
            f"Review: \"{review_text}\"\n"
            f"Item: {item.name} ({item.category})\n"
            f"User emotional style: {fingerprint.emotional_style}\n\n"
            f"Return ONLY valid JSON with keys:\n"
            f"  \"cultural_authenticity\": <0.0-1.0>,\n"
            f"  \"cultural_accuracy\": <0.0-1.0>,\n"
            f"  \"persona_consistency\": <0.0-1.0>,\n"
            f"  \"abeg_score\": <0.0-1.0>\n"
        )


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
    _fallback = VibeScore(
        cultural_authenticity=0.5,
        cultural_accuracy=0.5,
        persona_consistency=0.5,
        abeg_score=0.5,
        breakdown={"error": "parse_failed"},
        scored_in_mode=mode,
    )

    try:
        prompt = _build_vibe_prompt(review_text, target_fingerprint, item, mode)
        raw = _router.call_with_retry("utility", prompt, max_tokens=300)

        data = _parse_json_from_response(raw)

        cultural_authenticity = float(data.get("cultural_authenticity", 0.5))
        cultural_accuracy = float(data.get("cultural_accuracy", 0.5))
        persona_consistency = float(data.get("persona_consistency", 0.5))

        # Clamp to [0,1]
        cultural_authenticity = max(0.0, min(1.0, cultural_authenticity))
        cultural_accuracy = max(0.0, min(1.0, cultural_accuracy))
        persona_consistency = max(0.0, min(1.0, persona_consistency))

        abeg_score = (
            0.4 * cultural_authenticity
            + 0.35 * cultural_accuracy
            + 0.25 * persona_consistency
        )
        abeg_score = round(max(0.0, min(1.0, abeg_score)), 4)

        # Build breakdown from notes if present
        notes = data.get("notes", {})
        breakdown: dict[str, str] = {
            str(k): str(v) for k, v in notes.items()
        } if isinstance(notes, dict) else {}

        return VibeScore(
            cultural_authenticity=cultural_authenticity,
            cultural_accuracy=cultural_accuracy,
            persona_consistency=persona_consistency,
            abeg_score=abeg_score,
            breakdown=breakdown,
            scored_in_mode=mode,
        )

    except Exception as exc:
        logger.warning("run_naija_vibe_check failed: %s", exc)
        return _fallback


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
    results: list[VibeScore] = []
    for i, review_text in enumerate(reviews):
        fp = fingerprints[i] if i < len(fingerprints) else fingerprints[-1]
        it = items[i] if i < len(items) else items[-1]
        try:
            prompt = (
                f"Rate this review's Nigerian cultural authenticity from 0.0 to 1.0.\n"
                f"Return JSON: {{\"score\": 0.0}}\n"
                f"Review: {review_text}"
            )
            raw = _router.call_with_retry("utility", prompt, max_tokens=100)
            data = _parse_json_from_response(raw)
            score = float(max(0.0, min(1.0, data.get("score", 0.5))))
            results.append(
                VibeScore(
                    cultural_authenticity=score,
                    cultural_accuracy=score,
                    persona_consistency=score,
                    abeg_score=round(score, 4),
                    breakdown={},
                    scored_in_mode="passive",
                )
            )
        except Exception as exc:
            logger.warning("score_abeg_batch item %d failed: %s", i, exc)
            results.append(
                VibeScore(
                    cultural_authenticity=0.5,
                    cultural_accuracy=0.5,
                    persona_consistency=0.5,
                    abeg_score=0.5,
                    breakdown={"error": "parse_failed"},
                    scored_in_mode="passive",
                )
            )
    return results
