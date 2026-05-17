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
    from langgraph.graph import END, StateGraph
    from naijareview.agents.nodes.task_b_nodes import (
        apply_taxonomy_batch, bootstrap_fingerprint, check_user_history,
        cold_start_complete, cold_start_or_normal, cold_start_turn,
        compute_confidence, confidence_gate, detect_region,
        finalise, gen_clarifying_question, generate_explanations,
        build_fingerprint, load_history, retrieve_candidates,
        rerank, run_diversity_check,
    )

    graph: StateGraph = StateGraph(TaskBState)

    graph.add_node("check_user_history", check_user_history)
    graph.add_node("cold_start_turn", cold_start_turn)
    graph.add_node("load_history", load_history)
    graph.add_node("build_fingerprint", build_fingerprint)
    graph.add_node("detect_region", detect_region)
    graph.add_node("bootstrap_fingerprint", bootstrap_fingerprint)
    graph.add_node("retrieve_candidates", retrieve_candidates)
    graph.add_node("rerank", rerank)
    graph.add_node("run_diversity_check", run_diversity_check)
    graph.add_node("apply_taxonomy_batch", apply_taxonomy_batch)
    graph.add_node("generate_explanations", generate_explanations)
    graph.add_node("compute_confidence", compute_confidence)
    graph.add_node("finalise", finalise)
    graph.add_node("gen_clarifying_question", gen_clarifying_question)

    graph.set_entry_point("check_user_history")
    graph.add_conditional_edges(
        "check_user_history",
        cold_start_or_normal,
        {"cold_start_turn": "cold_start_turn", "load_history": "load_history"},
    )

    # Cold-start path: loop until persona complete, then bootstrap
    graph.add_conditional_edges(
        "cold_start_turn",
        cold_start_complete,
        {"bootstrap_fingerprint": "bootstrap_fingerprint", "cold_start_turn": END},
    )
    graph.add_edge("bootstrap_fingerprint", "retrieve_candidates")

    # Normal path: history → fingerprint → region → retrieve
    graph.add_edge("load_history", "build_fingerprint")
    graph.add_edge("build_fingerprint", "detect_region")
    graph.add_edge("detect_region", "retrieve_candidates")

    # Shared path: retrieve → rerank → diversity → taxonomy → explanations → confidence → gate
    graph.add_edge("retrieve_candidates", "rerank")
    graph.add_edge("rerank", "run_diversity_check")
    graph.add_edge("run_diversity_check", "apply_taxonomy_batch")
    graph.add_edge("apply_taxonomy_batch", "generate_explanations")
    graph.add_edge("generate_explanations", "compute_confidence")
    graph.add_conditional_edges(
        "compute_confidence",
        confidence_gate,
        {"finalise": "finalise", "gen_clarifying_question": "gen_clarifying_question"},
    )
    graph.add_edge("finalise", END)
    graph.add_edge("gen_clarifying_question", END)

    return graph.compile()
