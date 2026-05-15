"""Task B routes — POST /task-b/recommend.

Wired to stub agent by default. Replace ``get_agent`` dependency with real
LangGraph graph invocation when ready.

13.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from naijareview.api.deps import get_agent, get_optional_user
from naijareview.db.models import UserDB
from naijareview.eval.harness import AgentProtocol, TaskBInput, TaskBOutput
from naijareview.schemas.item import Item, Recommendation
from naijareview.schemas.output import RecommendationOutput

router = APIRouter()


# ── Request Schema ───────────────────────────────────────────────────────────


class TaskBRequest(BaseModel):
    """Request body for Task B recommendation."""

    user_id: str | None = None
    context_query: str
    conversation_history: list[dict] = []
    naija_vibe_mode: bool = False


# ── Route ────────────────────────────────────────────────────────────────────


@router.post("/recommend", response_model=RecommendationOutput)
async def recommend(
    body: TaskBRequest,
    agent: Annotated[AgentProtocol, Depends(get_agent)],
    current_user: Annotated[object | None, Depends(get_optional_user)] = None,
) -> RecommendationOutput:
    """Generate personalised recommendations with Nigerian cultural context.

    Supports cold-start (no user_id or no history) via the ``conversation_history``
    field — the agent runs the 3-turn onboarding flow automatically.

    **Stub behaviour (current):** Returns two hardcoded recommendations with
    zero confidence. Real behaviour is implemented when the LangGraph graph is
    wired via the ``get_agent`` dependency.
    """
    t0 = time.perf_counter()

    is_cold_start = body.user_id is None

    inp = TaskBInput(
        user_id=body.user_id or "cold_start",
        query=body.context_query,
        user_history=[],  # TODO: load from ChromaDB in real agent
        candidate_pool=[],  # TODO: retrieve from FAISS in real agent
        is_cold_start=is_cold_start,
        conversation_history=body.conversation_history,
        context={"naija_vibe_mode": body.naija_vibe_mode},
    )

    try:
        out: TaskBOutput = agent.run_task_b(inp)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Task B agent error: {exc}",
        ) from exc

    elapsed = (time.perf_counter() - t0) * 1000

    # Convert stub output to proper response schema
    recommendations = []
    for rank, r in enumerate(out.recommendations, start=1):
        item = Item(
            item_id=r.get("item_id", "unknown"),
            name=r.get("name", "Unknown"),
            category=r.get("category", "general"),
        )
        recommendations.append(
            Recommendation(
                item=item,
                rank=rank,
                explanation=r.get("reasoning", ""),
                alignment_dimensions=[],
            )
        )

    return RecommendationOutput(
        recommendations=recommendations,
        reasoning=out.reasoning,
        confidence=out.confidence,
        cold_start_mode=out.cold_start_mode,
        diversity_score=out.diversity_score,
        follow_up_question=out.clarifying_question,
        naija_vibe_mode_active=body.naija_vibe_mode,
    )
