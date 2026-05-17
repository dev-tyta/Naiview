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
    """Build and compile the Task A LangGraph."""
    from langgraph.graph import END, StateGraph
    from naijareview.agents.nodes.task_a_nodes import (
        analyse_item, apply_taxonomy, assemble_prompt, author_persona,
        build_fingerprint, decide_after_vibe_check, detect_region,
        fetch_few_shots, finalise_output, generate_draft,
        load_history, plan_regeneration, vibe_check,
    )

    graph: StateGraph = StateGraph(TaskAState)

    graph.add_node("load_history", load_history)
    graph.add_node("build_fingerprint", build_fingerprint)
    graph.add_node("detect_region", detect_region)
    graph.add_node("analyse_item", analyse_item)
    graph.add_node("apply_taxonomy", apply_taxonomy)
    graph.add_node("fetch_few_shots", fetch_few_shots)
    graph.add_node("author_persona", author_persona)
    graph.add_node("assemble_prompt", assemble_prompt)
    graph.add_node("generate_draft", generate_draft)
    graph.add_node("vibe_check", vibe_check)
    graph.add_node("plan_regeneration", plan_regeneration)
    graph.add_node("finalise_output", finalise_output)

    graph.set_entry_point("load_history")
    graph.add_edge("load_history", "build_fingerprint")
    graph.add_edge("build_fingerprint", "detect_region")
    graph.add_edge("detect_region", "analyse_item")
    graph.add_edge("analyse_item", "apply_taxonomy")
    graph.add_edge("apply_taxonomy", "fetch_few_shots")
    graph.add_edge("fetch_few_shots", "author_persona")
    graph.add_edge("author_persona", "assemble_prompt")
    graph.add_edge("assemble_prompt", "generate_draft")
    graph.add_edge("generate_draft", "vibe_check")
    graph.add_conditional_edges(
        "vibe_check",
        decide_after_vibe_check,
        {"plan_regeneration": "plan_regeneration", "finalise_output": "finalise_output"},
    )
    graph.add_edge("plan_regeneration", "author_persona")
    graph.add_edge("finalise_output", END)

    return graph.compile()
