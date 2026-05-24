"""Task B routes — POST /task-b/recommend, POST /task-b/cold-start."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_NODE_TITLES = {
    "check_user_history":      "User history checked",
    "cold_start_turn":         "Cold-start turn",
    "load_history":            "History loaded",
    "build_fingerprint":       "Fingerprint computed",
    "detect_region":           "Region detected",
    "bootstrap_fingerprint":   "Fingerprint bootstrapped",
    "retrieve_candidates":     "Candidates retrieved",
    "rerank":                  "Candidates reranked",
    "run_diversity_check":     "Diversity checked",
    "apply_taxonomy_batch":    "Taxonomy applied",
    "generate_explanations":   "Explanations generated",
    "compute_confidence":      "Confidence computed",
    "finalise":                "Recommendations finalised",
    "gen_clarifying_question": "Clarifying question generated",
}


def _get_graph():
    from naijareview.api.startup import get_task_b_graph
    g = get_task_b_graph()
    if g is None:
        from naijareview.agents.task_b import build_task_b_graph
        return build_task_b_graph()
    return g


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


def _recs_to_frontend(recs: list, overall_confidence: float = 0.8) -> list[dict]:
    result = []
    for rec in recs:
        item = rec.item
        cat_parts = [item.category]
        if item.nigerian_category and item.nigerian_category != item.category:
            cat_parts.append(item.nigerian_category)
        cat = " · ".join(cat_parts)
        match_pct = max(60, 100 - (rec.rank - 1) * 6)
        conf = round(max(0.5, overall_confidence * (1.0 - (rec.rank - 1) * 0.05)), 2)
        result.append({
            "name": item.name,
            "cat": cat,
            "match": match_pct,
            "confidence": conf,
            "reason": rec.explanation,
            "reasonVibe": rec.explanation,
        })
    return result


class TaskBRequest(BaseModel):
    """Request body for Task B recommendation.

    Accepts both frontend shape (persona/category/mood) and direct API shape
    (user_id/context_query/conversation_history).
    """

    # Frontend shape
    persona: str | None = None
    category: str | None = None
    mood: str | None = None

    # Direct API shape
    user_id: str | None = None
    context_query: str | None = None
    conversation_history: list[dict] = []

    naija_vibe_mode: bool = False


@router.post("/recommend")
async def recommend(body: TaskBRequest) -> dict:
    """Generate personalised recommendations with Nigerian cultural context."""
    user_id = body.user_id or body.persona or f"anon_{uuid.uuid4().hex}"

    if body.context_query:
        context_query = body.context_query
    else:
        parts: list[str] = []
        if body.category:
            parts.append(f"Looking for {body.category}")
        if body.mood:
            parts.append(body.mood)
        context_query = ". ".join(parts) if parts else "Nigerian food and entertainment recommendations"

    is_cold_start = not body.conversation_history

    initial_state = {
        "user_id": user_id,
        "context_query": context_query,
        "conversation_history": body.conversation_history,
        "naija_vibe_mode": body.naija_vibe_mode,
        "is_cold_start": is_cold_start,
        "cold_start_turn_count": len(body.conversation_history) // 2 if body.conversation_history else 0,
        "follow_up_turn_count": 0,
        "candidate_pool": [],
        "reranked_candidates": [],
        "recommendations": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task B graph error: {exc}") from exc

    overall_conf = float(final_state.get("confidence") or 0.8)
    recs = _recs_to_frontend(final_state.get("recommendations") or [], overall_conf)

    return {
        "recommendations": recs,
        "reasoning_trace": _trace_to_frontend(final_state.get("trace") or []),
        "diversity_score": float(final_state.get("diversity_score") or 0.0),
        "confidence": overall_conf,
        "follow_up_question": final_state.get("follow_up_question"),
        "naija_vibe_mode_active": body.naija_vibe_mode,
        "user_id": user_id,
    }


class ColdStartRequest(BaseModel):
    session_id: str
    turn_number: int = 3
    naija_vibe_mode: bool = False


@router.post("/cold-start")
async def cold_start(body: ColdStartRequest) -> dict:
    """Generate recommendations after the 3-turn client-side cold-start chat.

    The conversation happened in the browser; we bootstrap a generic Nigerian
    preference persona on the backend and return fresh personalised picks.
    """
    prefilled_history = [
        {"role": "user", "content": "I enjoy Nigerian food — jollof rice, suya, and local dishes"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Great! Do you value taste above all, or does price/value matter?",
            "parsed": {"food_preference": "Nigerian — jollof, suya, local dishes"},
        })},
        {"role": "user", "content": "Taste is important but I want good value too"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Last one — lively spot or quieter place?",
            "parsed": {"value_orientation": "balanced"},
        })},
        {"role": "user", "content": "Lively spots, affordable price range"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Perfect! Finding recommendations now...",
            "parsed": {"atmosphere_preference": "lively", "budget_range": "low"},
        })},
    ]

    initial_state = {
        "user_id": body.session_id,
        "context_query": "Nigerian food and entertainment recommendations",
        "conversation_history": prefilled_history,
        "naija_vibe_mode": body.naija_vibe_mode,
        "is_cold_start": True,
        "cold_start_turn_count": 3,
        "follow_up_turn_count": 0,
        "candidate_pool": [],
        "reranked_candidates": [],
        "recommendations": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cold-start error: {exc}") from exc

    overall_conf = float(final_state.get("confidence") or 0.8)
    recs = _recs_to_frontend(final_state.get("recommendations") or [], overall_conf)

    return {
        "done": True,
        "recommendations": recs,
        "reasoning_trace": _trace_to_frontend(final_state.get("trace") or []),
        "diversity_score": float(final_state.get("diversity_score") or 0.0),
    }
