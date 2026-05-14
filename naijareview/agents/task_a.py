"""Agent A — Review Generation (Task A).

Owner: Testimony
Full LangGraph specification: §6 of INTERNAL_ARCHITECTURE.md.

Graph flow:
  START → load_history → build_fingerprint → detect_region → analyse_item
  → apply_taxonomy → fetch_few_shots → author_persona → assemble_prompt
  → generate_draft → vibe_check → [conditional: finalise OR regenerate] → END
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from naijareview.schemas.item import Item
from naijareview.schemas.user import Fingerprint, RegionProfile, UserHistory
from naijareview.schemas.vibe import VibeScore


class TaskAState(TypedDict, total=False):
    """Typed state schema for Agent A. See §6.1."""

    # ─── Inputs (set by API handler) ───────────────────────
    user_id: str
    item: Item
    naija_vibe_mode: bool  # Default False

    # ─── Loaded / computed in-graph ────────────────────────
    user_history: Optional[UserHistory]
    fingerprint: Optional[Fingerprint]
    region_profile: Optional[RegionProfile]
    item_analysis: Optional[dict]  # Output of analyse_item_for_user
    few_shot_examples: list[str]
    persona_block: Optional[str]
    assembled_prompt: Optional[str]

    # ─── Generation state ──────────────────────────────────
    draft_review: Optional[str]
    draft_rating: Optional[float]
    vibe_score: Optional[VibeScore]
    retry_count: int  # Default 0
    regeneration_hint: Optional[str]  # Used to amplify next attempt

    # ─── Output ────────────────────────────────────────────
    final_review: Optional[str]
    final_rating: Optional[float]
    confidence: Optional[float]
    fingerprint_match_summary: Optional[str]
    style_notes: Optional[str]

    # ─── Error / diagnostic ────────────────────────────────
    errors: list[str]
    trace: list[dict]  # Per-node timing + outputs


def build_task_a_graph():
    """Build and compile the Task A LangGraph.

    Returns a compiled StateGraph ready for invocation.
    """
    # TODO: Implement — wire up nodes, conditional edges per §6.2
    raise NotImplementedError("Task A graph not yet implemented")
