"""Task B routes — POST /task-b/recommend.

See §13.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class TaskBRequest(BaseModel):
    """Request body for Task B recommendation."""

    user_id: str | None = None
    context_query: str
    conversation_history: list[dict] = []
    naija_vibe_mode: bool = False


@router.post("/recommend")
async def recommend(request: TaskBRequest) -> dict:
    """Generate personalised recommendations with Nigerian context.

    See §13.2 for full request/response contracts.
    """
    # TODO: Initialise TaskBState, invoke Agent B graph, return output
    raise HTTPException(status_code=501, detail="Task B not yet implemented")
