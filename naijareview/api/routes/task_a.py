"""Task A routes — POST /task-a/generate."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from naijareview.schemas.item import Item
from naijareview.schemas.user import Review

logger = logging.getLogger(__name__)

router = APIRouter()

_NODE_TITLES = {
    "load_history":      "User history loaded",
    "build_fingerprint": "Behavioural fingerprint computed",
    "detect_region":     "Region detected",
    "analyse_item":      "Item analysed",
    "apply_taxonomy":    "Nigerian taxonomy applied",
    "fetch_few_shots":   "Few-shot examples fetched",
    "author_persona":    "Author persona built",
    "assemble_prompt":   "Prompt assembled",
    "generate_draft":    "Draft generated",
    "vibe_check":        "Vibe Check completed",
    "plan_regeneration": "Regeneration planned",
    "finalise_output":   "Output finalised",
}


class ItemMetadata(BaseModel):
    name: str
    category: str
    description: str | None = None


class TaskARequest(BaseModel):
    """Request body for Task A review generation.

    Accepts both frontend shape (item_metadata) and direct API shape (item).
    ``user_id`` or ``persona`` can both identify the reviewer — if omitted a
    stable anon UUID is generated and returned so the caller can reuse it.
    """

    user_id: str | None = None
    persona: str | None = None
    item_metadata: ItemMetadata | None = None  # frontend shape
    item: Item | None = None                   # direct API shape
    naija_vibe_mode: bool = False


def _get_graph():
    from naijareview.api.startup import get_task_a_graph
    g = get_task_a_graph()
    if g is None:
        from naijareview.agents.task_a import build_task_a_graph
        return build_task_a_graph()
    return g


def _fingerprint_to_array(fp) -> list[dict]:
    if fp is None:
        return []
    topic_score = min(1.0, len(fp.topic_focus) / 3.0) if fp.topic_focus else 0.5
    return [
        {"dimension": "generosity",  "value": round(fp.generosity_score, 3)},
        {"dimension": "verbosity",   "value": round(fp.verbosity_score, 3)},
        {"dimension": "emotion",     "value": round(fp.emotional_intensity, 3)},
        {"dimension": "topic",       "value": round(topic_score, 3)},
        {"dimension": "consistency", "value": round(fp.consistency_score, 3)},
        {"dimension": "recency",     "value": round(fp.recency_weight, 3)},
        {"dimension": "naija",       "value": round(fp.naija_slang_index, 3)},
    ]


def _trace_to_frontend(trace: list[dict]) -> list[dict]:
    result = []
    for i, entry in enumerate(trace):
        node = entry.get("node", f"step_{i + 1}")
        summary = entry.get("summary", "")
        status = entry.get("status", "ok")
        duration_ms = entry.get("duration_ms", 0)
        title = _NODE_TITLES.get(node, node.replace("_", " ").title())
        detail = f"{summary} · {duration_ms:.0f}ms" if duration_ms and summary else summary or f"{duration_ms:.0f}ms"
        if status == "fallback":
            detail = f"fallback · {detail}"
        result.append({"step": i + 1, "title": title, "detail": detail})
    return result


def _persist_generated_review(
    user_id: str,
    item: Item,
    review_text: str,
    rating: float,
) -> None:
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
        if not ok:
            logger.warning("save_review returned False for user=%s", user_id)
    except Exception as exc:
        logger.warning("Failed to persist generated review for user=%s: %s", user_id, exc)


@router.post("/generate")
async def generate_review(body: TaskARequest) -> dict:
    """Generate a personalised review for a user on a given item."""
    user_id = body.user_id or f"anon_{uuid.uuid4().hex}"

    if body.item_metadata:
        item = Item(
            item_id=f"api_{uuid.uuid4().hex[:8]}",
            name=body.item_metadata.name,
            category=body.item_metadata.category,
            description=body.item_metadata.description,
        )
    elif body.item:
        item = body.item
    else:
        raise HTTPException(status_code=422, detail="Either item_metadata or item must be provided")

    initial_state = {
        "user_id": user_id,
        "item": item,
        "naija_vibe_mode": body.naija_vibe_mode,
        "retry_count": 0,
        "few_shot_examples": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task A graph error: {exc}") from exc

    review_text = final_state.get("final_review") or ""
    rating = float(final_state.get("final_rating") or 3.0)
    vibe = final_state.get("vibe_score")
    fp = final_state.get("fingerprint")

    if review_text:
        _persist_generated_review(user_id, item, review_text, rating)

    return {
        "review_text": review_text,
        "rating": rating,
        "confidence": float(final_state.get("confidence") or 0.0),
        "vibe_score": float(vibe.abeg_score) if vibe else None,
        "fingerprint": _fingerprint_to_array(fp),
        "fingerprint_match": final_state.get("fingerprint_match_summary") or "",
        "style_notes": final_state.get("style_notes") or "",
        "reasoning_trace": _trace_to_frontend(final_state.get("trace") or []),
        "user_id": user_id,
    }
