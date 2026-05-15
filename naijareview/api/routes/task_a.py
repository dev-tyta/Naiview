"""Task A routes — POST /task-a/generate.

Wired to stub agent by default. Replace ``get_agent`` dependency with real
LangGraph graph invocation when ready.

See §13.1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from naijareview.api.deps import get_agent, get_optional_user
from naijareview.db.models import UserDB
from naijareview.eval.harness import AgentProtocol, TaskAInput, TaskAOutput
from naijareview.schemas.item import Item
from naijareview.schemas.output import ReviewOutput

router = APIRouter()


# ── Request Schema ───────────────────────────────────────────────────────────


class TaskARequest(BaseModel):
    """Request body for Task A review generation."""

    user_id: str
    item: Item
    naija_vibe_mode: bool = False


# ── Route ────────────────────────────────────────────────────────────────────


@router.post("/generate", response_model=ReviewOutput)
async def generate_review(
    body: TaskARequest,
    agent: Annotated[AgentProtocol, Depends(get_agent)],
    current_user: Annotated[object | None, Depends(get_optional_user)] = None,
) -> ReviewOutput:
    """Generate a personalised review for a user on a given item.

    When ``naija_vibe_mode=True``, the Vibe Checker runs in active mode and
    may trigger regeneration if the Abeg score is below threshold.

    **Stub behaviour (current):** Returns a hardcoded review with zero
    confidence. Real behaviour is implemented when the LangGraph graph is
    wired via the ``get_agent`` dependency.
    """
    t0 = time.perf_counter()

    # Build stub input (real agent will use full user history from ChromaDB)
    inp = TaskAInput(
        user_id=body.user_id,
        item_id=body.item.item_id,
        item_metadata=body.item.model_dump(),
        user_history=[],  # TODO: load from ChromaDB in real agent
        context={"naija_vibe_mode": body.naija_vibe_mode},
    )

    try:
        out: TaskAOutput = agent.run_task_a(inp)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Task A agent error: {exc}",
        ) from exc

    elapsed = (time.perf_counter() - t0) * 1000

    # Convert stub output to proper response schema
    return ReviewOutput(
        generated_review=out.generated_review,
        predicted_rating=out.predicted_rating,
        confidence=out.confidence,
        fingerprint_match=out.fingerprint_match,
        style_notes=out.style_notes,
        abeg_score=out.abeg_score,
        vibe_breakdown=None,
        naija_vibe_mode_active=body.naija_vibe_mode,
        retry_count=0,
    )
