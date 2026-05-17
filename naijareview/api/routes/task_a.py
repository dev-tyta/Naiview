"""Task A routes — POST /task-a/generate.

See §13.1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from naijareview.schemas.item import Item
from naijareview.schemas.output import ReviewOutput
from naijareview.schemas.user import Review

logger = logging.getLogger(__name__)

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        from naijareview.agents.task_a import build_task_a_graph

        _graph = build_task_a_graph()
    return _graph


class TaskARequest(BaseModel):
    """Request body for Task A review generation.

    ``user_id`` is optional. If omitted a UUID is generated and returned in
    the response — store it client-side and pass on future calls to accumulate
    history and personalise outputs over time.
    """

    user_id: str | None = None
    item: Item
    naija_vibe_mode: bool = False


def _persist_generated_review(
    user_id: str,
    item: Item,
    review_text: str,
    rating: float,
) -> None:
    """Save generated review to ChromaDB so it builds user history over time.

    Tagged with source='generated' in metadata. Non-blocking — failures are
    logged but do not affect the API response.
    """
    try:
        from naijareview.tools.memory import save_review

        review = Review(
            review_id=f"gen_{uuid.uuid4().hex}",
            user_id=user_id,
            item_id=item.item_id,
            text=review_text,
            stars=max(1.0, min(5.0, rating)),
            timestamp=datetime.now(),
            item_category=item.nigerian_category or item.category,
        )
        ok = save_review.invoke({"review": review})
        if ok:
            logger.info("Generated review persisted for user=%s item=%s", user_id, item.item_id)
        else:
            logger.warning("save_review returned False for user=%s", user_id)
    except Exception as exc:
        logger.warning("Failed to persist generated review for user=%s: %s", user_id, exc)


@router.post("/generate", response_model=ReviewOutput)
async def generate_review(body: TaskARequest) -> ReviewOutput:
    """Generate a personalised review for a user on a given item.

    Generated review is saved to ChromaDB after generation so that repeated
    calls for the same user accumulate history — new users graduate from
    cold-start to fingerprint-based generation after 3+ reviews.

    Graph flow:
    load_history → build_fingerprint → detect_region → analyse_item
    → apply_taxonomy → fetch_few_shots → author_persona → assemble_prompt
    → generate_draft → vibe_check → [finalise | plan_regeneration loop]
    """
    user_id = body.user_id or f"anon_{uuid.uuid4().hex}"

    initial_state = {
        "user_id": user_id,
        "item": body.item,
        "naija_vibe_mode": body.naija_vibe_mode,
        "retry_count": 0,
        "few_shot_examples": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task A graph error: {exc}") from exc

    review_text = final_state.get("final_review", "") or ""
    rating = float(final_state.get("final_rating", 3.0))
    vibe = final_state.get("vibe_score")

    if review_text:
        _persist_generated_review(user_id, body.item, review_text, rating)

    return ReviewOutput(
        generated_review=review_text,
        predicted_rating=rating,
        confidence=float(final_state.get("confidence", 0.0)),
        fingerprint_match=final_state.get("fingerprint_match_summary") or "",
        style_notes=final_state.get("style_notes") or "",
        abeg_score=float(vibe.abeg_score) if vibe else None,
        vibe_breakdown={
            "cultural_authenticity": float(vibe.cultural_authenticity),
            "cultural_accuracy": float(vibe.cultural_accuracy),
            "persona_consistency": float(vibe.persona_consistency),
        }
        if vibe
        else None,
        naija_vibe_mode_active=body.naija_vibe_mode,
        retry_count=final_state.get("retry_count", 0),
        user_id=user_id,
    )
