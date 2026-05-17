"""Task A routes — POST /task-a/generate.

See §13.1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from naijareview.schemas.item import Item
from naijareview.schemas.output import ReviewOutput

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        from naijareview.agents.task_a import build_task_a_graph

        _graph = build_task_a_graph()
    return _graph


class TaskARequest(BaseModel):
    """Request body for Task A review generation."""

    user_id: str
    item: Item
    naija_vibe_mode: bool = False


@router.post("/generate", response_model=ReviewOutput)
async def generate_review(body: TaskARequest) -> ReviewOutput:
    """Generate a personalised review for a user on a given item.

    Invokes the Task A LangGraph:
    load_history → build_fingerprint → detect_region → analyse_item
    → apply_taxonomy → fetch_few_shots → author_persona → assemble_prompt
    → generate_draft → vibe_check → [finalise | plan_regeneration loop]

    See §13.1 for full request/response contracts.
    """
    initial_state = {
        "user_id": body.user_id,
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

    vibe = final_state.get("vibe_score")
    return ReviewOutput(
        generated_review=final_state.get("final_review") or "",
        predicted_rating=final_state.get("final_rating") or 0.0,
        confidence=final_state.get("confidence") or 0.0,
        fingerprint_match=final_state.get("fingerprint_match_summary") or "",
        style_notes=final_state.get("style_notes") or "",
        abeg_score=float(vibe.abeg_score) if vibe else None,
        vibe_breakdown=vibe.breakdown if vibe else None,
        naija_vibe_mode_active=body.naija_vibe_mode,
        retry_count=final_state.get("retry_count", 0),
    )
