"""Task B routes — POST /task-b/recommend, POST /task-b/cold-start."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_NODE_TITLES = {
    "check_user_history":      "User history checked",
    "cold_start_turn":         "Cold-start turn",
    "load_history":            "History loaded",
    "build_fingerprint":       "Fingerprint computed",
    "detect_region":           "Region detected",
    "bootstrap_fingerprint":   "Fingerprint bootstrapped",
    "retrieve_candidates":     "Candidates retrieved",
    "rerank":                  "Candidates reranked",
    "run_diversity_check":     "Diversity checked",
    "apply_taxonomy_batch":    "Taxonomy applied",
    "generate_explanations":   "Explanations generated",
    "compute_confidence":      "Confidence computed",
    "finalise":                "Recommendations finalised",
    "gen_clarifying_question": "Clarifying question generated",
}


def _get_graph():
    from naijareview.api.startup import get_task_b_graph
    g = get_task_b_graph()
    if g is None:
        from naijareview.agents.task_b import build_task_b_graph
        return build_task_b_graph()
    return g


async def _generate_persona_profile(category: str, mood: str, naija_vibe: bool) -> dict:
    """Use LLM to generate a realistic Nigerian user persona from category + mood context."""
    import re as _re
    from naijareview.llm.router import LLMRouter
    _router = LLMRouter()

    register = "casual Naija / Pidgin tone" if naija_vibe else "natural, conversational Nigerian English"
    prompt = (
        f"You are building a realistic Nigerian user persona for a recommendation system.\n"
        f"Category: {category}\n"
        f"User's request/mood: {mood}\n\n"
        f"Generate a natural persona — what a real Nigerian would say during a 3-turn preference interview.\n"
        f"Use {register} for the user responses.\n\n"
        f"Return ONLY valid JSON:\n"
        '{"category_preference": "<specific preference string for this category>", '
        '"value_orientation": "taste_first|value_first|balanced", '
        '"atmosphere": "lively|quiet|either", '
        '"budget": "low|mid|high", '
        '"turn2_response": "<how user responds to quality vs value question, 1 sentence>", '
        '"turn3_response": "<how user responds to atmosphere + budget question, 1 sentence>"}'
    )

    try:
        raw = await asyncio.to_thread(_router.call_with_retry, "utility", prompt, 300)
        raw = raw.strip()
        cleaned = _re.sub(r"```(?:json)?", "", raw).rstrip("`").strip()
        m = _re.search(r"\{.*\}", cleaned, _re.DOTALL)
        data = json.loads(m.group() if m else cleaned)
        required = ["category_preference", "value_orientation", "atmosphere", "budget", "turn2_response", "turn3_response"]
        if all(k in data for k in required):
            return data
    except Exception:
        pass

    # Fallback persona if LLM fails
    return {
        "category_preference": f"{category} — {mood[:80]}" if mood else category,
        "value_orientation": "balanced",
        "atmosphere": "lively" if any(w in mood.lower() for w in ["lively", "buzzing", "night", "squad"]) else "either",
        "budget": "mid",
        "turn2_response": "Quality is important but value for money matters too",
        "turn3_response": "Good atmosphere, mid-range budget works for me",
    }


def _trace_to_frontend(trace: list[dict]) -> list[dict]:
    result = []
    for i, entry in enumerate(trace):
        node = entry.get("node", f"step_{i + 1}")
        summary = entry.get("summary", "")
        status = entry.get("status", "ok")
        duration_ms = entry.get("duration_ms", 0)
        title = _NODE_TITLES.get(node, node.replace("_", " ").title())
        detail = f"{summary} · {duration_ms:.0f}ms" if duration_ms and summary else summary or f"{duration_ms:.0f}ms"
        if status == "fallback":
            detail = f"fallback · {detail}"
        result.append({"step": i + 1, "title": title, "detail": detail})
    return result


def _recs_to_frontend(recs: list, overall_confidence: float = 0.8) -> list[dict]:
    result = []
    for rec in recs:
        item = rec.item
        cat_parts = [item.category]
        if item.nigerian_category and item.nigerian_category != item.category:
            cat_parts.append(item.nigerian_category)
        cat = " · ".join(cat_parts)
        match_pct = max(60, 100 - (rec.rank - 1) * 6)
        conf = round(max(0.5, overall_confidence * (1.0 - (rec.rank - 1) * 0.05)), 2)
        result.append({
            "name": item.name,
            "cat": cat,
            "match": match_pct,
            "confidence": conf,
            "reason": rec.explanation,
            "reasonVibe": rec.explanation,
        })
    return result



class TaskBRequest(BaseModel):
    """Request body for Task B recommendation.

    Accepts both frontend shape (persona/category/mood) and direct API shape
    (user_id/context_query/conversation_history).
    """

    # Frontend shape
    persona: str | None = None
    category: str | None = None
    mood: str | None = None

    # Direct API shape
    user_id: str | None = None
    context_query: str | None = None
    conversation_history: list[dict] = []

    naija_vibe_mode: bool = False


@router.post("/recommend")
async def recommend(body: TaskBRequest) -> dict:
    """Generate personalised recommendations with Nigerian cultural context."""
    user_id = body.user_id or body.persona or f"anon_{uuid.uuid4().hex}"

    if body.context_query:
        context_query = body.context_query
    else:
        parts: list[str] = []
        if body.category:
            parts.append(f"Looking for {body.category}")
        if body.mood:
            parts.append(body.mood)
        context_query = ". ".join(parts) if parts else "Nigerian food and entertainment recommendations"

    # When a persona/category/mood is given but no real conversation history exists,
    # pre-fill a completed 3-turn cold-start exchange so the graph can produce
    # recommendations without a back-and-forth interaction.
    convo_history = body.conversation_history
    cold_start_turns = len(convo_history) // 2 if convo_history else 0

    if not convo_history and (body.persona or body.category or body.mood):
        ctx = _resolve_category_context(body.category)
        mood_text = body.mood or ""
        naija_tone = "casual Naija style" if body.naija_vibe_mode else "friendly English"

        # Use LLM to generate a realistic Nigerian persona from category + mood
        persona_profile = await _generate_persona_profile(
            category=body.category or ctx["query"].split()[0],
            mood=mood_text or ctx["pref_val"],
            naija_vibe=body.naija_vibe_mode,
        )
        category_pref = persona_profile["category_preference"]
        atmosphere = persona_profile["atmosphere"]
        budget = persona_profile["budget"]
        value = persona_profile["value_orientation"]
        turn2_user = persona_profile["turn2_response"]
        turn3_user = persona_profile["turn3_response"]

        convo_history = [
            {"role": "user", "content": f"I enjoy {category_pref}"},
            {"role": "assistant", "content": json.dumps({
                "agent_utterance": "Nice! Any particular vibe — taste first, value for money, or a balance?",
                "parsed": {"food_preference": category_pref},
            })},
            {"role": "user", "content": turn2_user},
            {"role": "assistant", "content": json.dumps({
                "agent_utterance": "Noted! Lively or quieter spots? What's your budget like?",
                "parsed": {"food_preference": category_pref, "value_orientation": value},
            })},
            {"role": "user", "content": turn3_user},
            {"role": "assistant", "content": json.dumps({
                "agent_utterance": "Perfect! Let me find some great recommendations for you...",
                "parsed": {"food_preference": category_pref, "value_orientation": value,
                           "atmosphere_preference": atmosphere, "budget_range": budget},
            })},
        ]
        cold_start_turns = 3

    initial_state = {
        "user_id": user_id,
        "context_query": context_query,
        "conversation_history": convo_history,
        "naija_vibe_mode": body.naija_vibe_mode,
        "is_cold_start": True,
        "cold_start_turn_count": cold_start_turns,
        "follow_up_turn_count": 0,
        "candidate_pool": [],
        "reranked_candidates": [],
        "recommendations": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task B graph error: {exc}") from exc

    overall_conf = float(final_state.get("confidence") or 0.8)
    recs = _recs_to_frontend(final_state.get("recommendations") or [], overall_conf)

    return {
        "recommendations": recs,
        "reasoning_trace": _trace_to_frontend(final_state.get("trace") or []),
        "diversity_score": float(final_state.get("diversity_score") or 0.0),
        "confidence": overall_conf,
        "follow_up_question": final_state.get("follow_up_question"),
        "naija_vibe_mode_active": body.naija_vibe_mode,
        "user_id": user_id,
    }


class ColdStartRequest(BaseModel):
    session_id: str
    turn_number: int = 3
    naija_vibe_mode: bool = False
    category: str | None = None
    conversation_summary: str | None = None


_CATEGORY_CONTEXT: dict[str, dict] = {
    "food": {
        "pref_key": "food_preference",
        "pref_val": "Nigerian food — jollof rice, suya, and local dishes",
        "query": "Nigerian food and restaurant recommendations",
    },
    "salon & spa": {
        "pref_key": "food_preference",
        "pref_val": "hair and beauty salon services",
        "query": "hair salon, spa, and grooming services in Nigeria",
    },
    "tech": {
        "pref_key": "food_preference",
        "pref_val": "technology products and gadgets",
        "query": "tech products, gadgets, and electronics in Nigeria",
    },
    "services": {
        "pref_key": "food_preference",
        "pref_val": "professional services",
        "query": "professional and home services in Nigeria",
    },
    "entertainment": {
        "pref_key": "food_preference",
        "pref_val": "entertainment and leisure activities",
        "query": "entertainment venues and leisure activities in Nigeria",
    },
}


def _resolve_category_context(category: str | None) -> dict:
    if not category:
        return _CATEGORY_CONTEXT["food"]
    return _CATEGORY_CONTEXT.get(category.lower(), {
        "pref_key": "food_preference",
        "pref_val": category,
        "query": f"{category} recommendations in Nigeria",
    })


@router.post("/cold-start")
async def cold_start(body: ColdStartRequest) -> dict:
    """Generate recommendations after the 3-turn client-side cold-start chat.

    The conversation happened in the browser; we bootstrap a generic Nigerian
    preference persona on the backend and return fresh personalised picks.
    """
    ctx = _resolve_category_context(body.category)
    pref_val = body.conversation_summary or ctx["pref_val"]
    context_query = f"{body.category or 'Nigerian'} recommendations — {pref_val}" if body.category else ctx["query"]

    prefilled_history = [
        {"role": "user", "content": f"I'm looking for {pref_val}"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Great! Do you value quality above all, or does price/value matter?",
            "parsed": {ctx["pref_key"]: pref_val},
        })},
        {"role": "user", "content": "Quality is important but I want good value too"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Last one — lively spot or quieter place?",
            "parsed": {"value_orientation": "balanced"},
        })},
        {"role": "user", "content": "Lively spots, affordable price range"},
        {"role": "assistant", "content": json.dumps({
            "agent_utterance": "Perfect! Finding recommendations now...",
            "parsed": {"atmosphere_preference": "lively", "budget_range": "low"},
        })},
    ]

    initial_state = {
        "user_id": body.session_id,
        "context_query": context_query,
        "conversation_history": prefilled_history,
        "naija_vibe_mode": body.naija_vibe_mode,
        "is_cold_start": True,
        "cold_start_turn_count": 3,
        "follow_up_turn_count": 0,
        "candidate_pool": [],
        "reranked_candidates": [],
        "recommendations": [],
        "errors": [],
        "trace": [],
    }

    try:
        graph = _get_graph()
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cold-start error: {exc}") from exc

    overall_conf = float(final_state.get("confidence") or 0.8)
    recs = _recs_to_frontend(final_state.get("recommendations") or [], overall_conf)

    return {
        "done": True,
        "recommendations": recs,
        "reasoning_trace": _trace_to_frontend(final_state.get("trace") or []),
        "diversity_score": float(final_state.get("diversity_score") or 0.0),
    }
