"""Task A routes — POST /task-a/generate.

See §13.1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from naijareview.schemas.item import Item

router = APIRouter()


class TaskARequest(BaseModel):
    """Request body for Task A review generation."""

    user_id: str
    item: Item
    naija_vibe_mode: bool = False


@router.post("/generate")
async def generate_review(request: TaskARequest) -> dict:
    """Generate a personalised Nigerian-contextualised review.

    See §13.1 for full request/response contracts.
    """
    # TODO: Initialise TaskAState, invoke Agent A graph, return output
    raise HTTPException(status_code=501, detail="Task A not yet implemented")
