"""Agent B — Recommendation (Task B).

Owner: Aaliyah
Full LangGraph specification: §7 of INTERNAL_ARCHITECTURE.md.

Graph flow:
  START → check_user_history → [cold_start OR normal path]
  Normal: load_history → build_fingerprint → detect_region
  Cold-start: cold_start_turn → [persona complete? → bootstrap_fingerprint OR END]
  Both merge → retrieve_candidates → rerank → diversity_check
  → apply_taxonomy_batch → generate_explanations → compute_confidence
  → [confidence_gate: finalise OR gen_clarifying_question] → END
"""

from __future__ import annotations

from typing import Optional, TypedDict

from naijareview.schemas.item import Item, RankedItem, Recommendation
from naijareview.schemas.persona import ColdStartPersona
from naijareview.schemas.user import Fingerprint, RegionProfile, UserHistory


class TaskBState(TypedDict, total=False):
    """Typed state schema for Agent B. See §7.1."""

    # ─── Inputs ────────────────────────────────────────────
    user_id: Optional[str]  # None for cold-start
    context_query: str  # What they want now
    conversation_history: list[dict]  # For multi-turn
    naija_vibe_mode: bool  # Affects explanation tone

    # ─── Loaded / computed in-graph ────────────────────────
    user_history: Optional[UserHistory]
    fingerprint: Optional[Fingerprint]
    region_profile: Optional[RegionProfile]
    is_cold_start: bool
    cold_start_persona: Optional[ColdStartPersona]
    cold_start_turn_count: int  # Default 0

    # ─── Retrieval & ranking state ─────────────────────────
    candidate_pool: list[Item]  # Top-20 raw
    reranked_candidates: list[RankedItem]
    diversity_score: Optional[float]

    # ─── Output ────────────────────────────────────────────
    recommendations: list[Recommendation]
    reasoning: Optional[str]
    confidence: Optional[float]
    follow_up_question: Optional[str]  # If conf < threshold
    follow_up_turn_count: int  # Default 0

    # ─── Diagnostic ────────────────────────────────────────
    errors: list[str]
    trace: list[dict]


def build_task_b_graph():
    """Build and compile the Task B LangGraph.

    Returns a compiled StateGraph ready for invocation.
    """
    # TODO: Implement — wire up nodes, conditional edges per §7.2
    raise NotImplementedError("Task B graph not yet implemented")
