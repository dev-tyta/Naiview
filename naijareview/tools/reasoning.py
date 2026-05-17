"""Reasoning tools: analyse_item_for_user, rerank_candidates.

See §4.5 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from langchain_core.tools import tool

from naijareview.llm.router import LLMRouter
from naijareview.schemas.item import Item, RankedItem
from naijareview.schemas.user import Fingerprint

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
_router = LLMRouter()


def _parse_json_from_response(text: str) -> dict | list:
    """Extract and parse the first JSON object or array from an LLM response."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Try to find a JSON array first, then object
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(cleaned)


@tool
def analyse_item_for_user(item: Item, fingerprint: Fingerprint) -> dict:
    """LLM-backed analysis of how an item maps to a user's preferences.

    Used in Task A before generation.
    LLM tier: Haiku (utility task).

    Args:
        item: The item to analyse.
        fingerprint: The user's behavioural fingerprint.

    Returns:
        Dict with keys: inferred_sentiment, relevant_topics,
        predicted_rating_range, reasoning.
    """
    _fallback = {
        "inferred_sentiment": "neutral",
        "relevant_topics": fingerprint.topic_focus[:2],
        "predicted_rating_range": "3-4 stars",
        "reasoning": "Fallback analysis",
    }

    # Determine generosity label
    if fingerprint.generosity_score > 0.6:
        generosity_label = "high"
    elif fingerprint.generosity_score > 0.4:
        generosity_label = "average"
    else:
        generosity_label = "low"

    topic_str = ", ".join(fingerprint.topic_focus) if fingerprint.topic_focus else "general"

    prompt = (
        f"Analyse how this item matches this user's preferences.\n"
        f"Item: {item.name}, category: {item.category}, "
        f"avg_rating: {item.avg_rating:.1f}.\n"
        f"User likes: {topic_str}, is {fingerprint.emotional_style}, "
        f"gives {generosity_label} ratings.\n\n"
        f"Return ONLY valid JSON with keys:\n"
        f"  \"inferred_sentiment\": \"positive\", \"negative\", or \"neutral\",\n"
        f"  \"relevant_topics\": [list of 2-3 strings],\n"
        f"  \"predicted_rating_range\": \"string like '3-4 stars'\",\n"
        f"  \"reasoning\": \"one sentence\"\n"
    )

    try:
        raw = _router.call_with_retry("utility", prompt, max_tokens=200)
        data = _parse_json_from_response(raw)
        if not isinstance(data, dict):
            return _fallback

        return {
            "inferred_sentiment": str(data.get("inferred_sentiment", "neutral")),
            "relevant_topics": list(data.get("relevant_topics", fingerprint.topic_focus[:2])),
            "predicted_rating_range": str(data.get("predicted_rating_range", "3-4 stars")),
            "reasoning": str(data.get("reasoning", "Fallback analysis")),
        }

    except Exception as exc:
        logger.warning("analyse_item_for_user failed: %s", exc)
        return _fallback


@tool
def rerank_candidates(
    candidates: list[Item],
    fingerprint: Fingerprint,
    context_query: str,
) -> list[RankedItem]:
    """LLM-backed chain-of-thought reranking of top-20 candidates.

    LLM tier: Sonnet 4 (quality-critical).

    Args:
        candidates: Top-20 candidate items from retrieval.
        fingerprint: The user's behavioural fingerprint.
        context_query: What the user wants right now.

    Returns:
        List of RankedItems sorted by alignment_score descending.
    """
    if not candidates:
        return []

    def _default_ranked() -> list[RankedItem]:
        n = len(candidates)
        return [
            RankedItem(
                item=c,
                rank=i + 1,
                alignment_score=round((n - i) / n, 4),
                reasoning_snippet="Default ordering.",
            )
            for i, c in enumerate(candidates)
        ]

    # Try the Jinja template as a static string reference; build prompt manually
    template_path = _PROMPTS_DIR / "task_b_rerank.jinja"
    try:
        # Build a numbered candidate list
        candidate_lines = "\n".join(
            f"{i + 1}. {c.name} ({c.category}, {c.avg_rating:.1f} stars)"
            for i, c in enumerate(candidates)
        )

        topic_str = ", ".join(fingerprint.topic_focus) if fingerprint.topic_focus else "general"

        prompt = (
            f"Rerank these {len(candidates)} items for a user with the following profile:\n"
            f"- Topic interests: {topic_str}\n"
            f"- Emotional style: {fingerprint.emotional_style}\n"
            f"- Generosity score: {fingerprint.generosity_score:.2f} (0=low rater, 1=high rater)\n"
            f"- Current request: \"{context_query}\"\n\n"
            f"CANDIDATES:\n{candidate_lines}\n\n"
            f"Return ONLY valid JSON with a 'rankings' array. Each element must have:\n"
            f"  \"item_index\": <1-based integer>,\n"
            f"  \"rank\": <1-based integer>,\n"
            f"  \"alignment_score\": <0.0-1.0>,\n"
            f"  \"reasoning_snippet\": \"<one concise sentence>\"\n"
            f"\nExample: {{\"rankings\": [{{\"item_index\": 2, \"rank\": 1, "
            f"\"alignment_score\": 0.92, \"reasoning_snippet\": \"Best match.\"}}]}}"
        )

        raw = _router.call_with_retry("generation", prompt, max_tokens=600)
        data = _parse_json_from_response(raw)

        if not isinstance(data, dict) or "rankings" not in data:
            logger.warning("rerank_candidates: unexpected response shape")
            return _default_ranked()

        rankings: list[dict] = data["rankings"]
        if not rankings:
            return _default_ranked()

        # Sort by rank ascending
        rankings_sorted = sorted(rankings, key=lambda x: int(x.get("rank", 999)))

        result: list[RankedItem] = []
        n = len(candidates)
        for entry in rankings_sorted:
            idx = int(entry.get("item_index", 0)) - 1  # convert 1-based to 0-based
            if idx < 0 or idx >= n:
                continue
            rank = int(entry.get("rank", len(result) + 1))
            alignment_score = float(
                max(0.0, min(1.0, entry.get("alignment_score", (n - rank) / n)))
            )
            reasoning_snippet = str(
                entry.get("reasoning_snippet", "Ranked by user preference alignment.")
            )
            result.append(
                RankedItem(
                    item=candidates[idx],
                    rank=rank,
                    alignment_score=alignment_score,
                    reasoning_snippet=reasoning_snippet,
                )
            )

        # Fill in any candidates not returned by LLM (append at the end)
        returned_indices = {int(e.get("item_index", 0)) - 1 for e in rankings_sorted}
        next_rank = len(result) + 1
        for i, c in enumerate(candidates):
            if i not in returned_indices:
                result.append(
                    RankedItem(
                        item=c,
                        rank=next_rank,
                        alignment_score=round((n - next_rank) / max(n, 1), 4),
                        reasoning_snippet="Not explicitly ranked by LLM.",
                    )
                )
                next_rank += 1

        return result

    except Exception as exc:
        logger.warning("rerank_candidates failed: %s", exc)
        return _default_ranked()
