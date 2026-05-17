"""Task B routes — POST /task-b/recommend."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from naijareview.schemas.output import RecommendationOutput

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        from naijareview.agents.task_b import build_task_b_graph
        _graph = build_task_b_graph()
    return _graph


class TaskBRequest(BaseModel):
    """Request body for Task B recommendation.

    ``user_id`` is optional. If omitted a UUID is generated and returned in
    the response — store it client-side and reuse to build preference history.
    """

    user_id: str | None = None
    context_query: str
    conversation_history: list[dict] = []
    naija_vibe_mode: bool = False


@router.post("/recommend", response_model=RecommendationOutput)
async def recommend(body: TaskBRequest) -> RecommendationOutput:
    """Generate personalised recommendations with Nigerian cultural context."""

    # Preserve None so the graph knows this is a brand-new session (cold-start path)
    # but still have a stable ID to return to the caller
    user_id = body.user_id or f"anon_{uuid.uuid4().hex}"
    is_cold_start = body.user_id is None  # True only when caller provided no ID

    initial_state = {
        "user_id": user_id,
        "context_query": body.context_query,
        "conversation_history": body.conversation_history,
        "naija_vibe_mode": body.naija_vibe_mode,
        "is_cold_start": is_cold_start,
        "cold_start_turn_count": 0,
        "follow_up_turn_count": 0,
        "candidate_pool": [],
        "reranked_candidates": [],
        "recommendations": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task B graph error: {exc}") from exc

    return RecommendationOutput(
        recommendations=final_state.get("recommendations", []),
        reasoning=final_state.get("reasoning"),
        confidence=final_state.get("confidence"),
        cold_start_mode=final_state.get("is_cold_start", False),
        diversity_score=float(final_state.get("diversity_score", 0.0)),
        follow_up_question=final_state.get("follow_up_question"),
        naija_vibe_mode_active=body.naija_vibe_mode,
        user_id=user_id,
    )
