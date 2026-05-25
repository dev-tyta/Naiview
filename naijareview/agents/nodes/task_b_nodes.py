"""Task B node implementations.

Owner: Aaliyah
See §7 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Literal

from naijareview.agents.nodes.shared import append_error
from naijareview.llm.router import LLMRouter
from naijareview.skills.memory_bootstrap import ColdStartBootstrapper
from naijareview.agents.task_b import TaskBState

logger = logging.getLogger(__name__)
_router = LLMRouter()


def _ts() -> float:
    return time.time()


def _trace(state: "TaskBState", node: str, started: float, summary: str, status: str = "ok") -> "TaskBState":
    entry = {
        "node": node,
        "started_at": started,
        "duration_ms": round((time.time() - started) * 1000, 1),
        "status": status,
        "summary": summary,
    }
    return {**state, "trace": [*state.get("trace", []), entry]}


# ── Nodes ─────────────────────────────────────────────────────────────────────

def check_user_history(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.memory import load_user_history
        user_id = state.get("user_id")
        is_cold = True

        if user_id:
            history = load_user_history.invoke({"user_id": user_id})
            is_cold = not history.has_sufficient_history
            state = {**state, "user_history": history, "is_cold_start": is_cold}
        else:
            state = {**state, "is_cold_start": True}

        return _trace(state, "check_user_history", t0, f"cold_start={is_cold}")
    except Exception as exc:
        logger.warning("check_user_history failed: %s", exc)
        state = append_error({**state, "is_cold_start": True}, f"check_user_history: {exc}")
        return _trace(state, "check_user_history", t0, "fallback: cold start", "error")


def cold_start_or_normal(state: "TaskBState") -> Literal["cold_start_turn", "load_history"]:
    """Conditional edge: route to cold-start flow or normal flow."""
    return "cold_start_turn" if state.get("is_cold_start", True) else "load_history"


def cold_start_turn(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        naija = state.get("naija_vibe_mode", False)
        bootstrapper = ColdStartBootstrapper(llm_router=_router, naija_vibe_mode=naija)
        history = state.get("conversation_history", [])
        utterance, persona = bootstrapper.next_turn(history)

        updated_history = [*history, {"role": "assistant", "content": utterance}]
        state = {**state, "conversation_history": updated_history}

        if persona is not None:
            state = {**state, "cold_start_persona": persona}

        turn_count = state.get("cold_start_turn_count", 0) + 1
        state = {**state, "cold_start_turn_count": turn_count}
        return _trace(state, "cold_start_turn", t0, f"turn={turn_count} persona_complete={persona is not None}")
    except Exception as exc:
        logger.warning("cold_start_turn failed: %s", exc)
        state = append_error(state, f"cold_start_turn: {exc}")
        return _trace(state, "cold_start_turn", t0, "cold start turn failed", "error")


def cold_start_complete(state: "TaskBState") -> Literal["bootstrap_fingerprint", "cold_start_turn"]:
    """Conditional edge after cold_start_turn: done or need more turns."""
    persona = state.get("cold_start_persona")
    if persona is not None and persona.turns_completed >= 3:
        return "bootstrap_fingerprint"
    return "cold_start_turn"


def load_history(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.memory import load_user_history
        history = load_user_history.invoke({"user_id": state["user_id"]})
        state = {**state, "user_history": history}
        return _trace(state, "load_history", t0, f"{history.review_count} reviews")
    except Exception as exc:
        logger.warning("load_history failed: %s", exc)
        state = append_error(state, f"load_history: {exc}")
        return _trace(state, "load_history", t0, "fallback: empty history", "error")


def build_fingerprint(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.fingerprint import build_behavioural_fingerprint
        from naijareview.memory.semantic import FingerprintCache
        history = state.get("user_history")
        if history is None:
            raise ValueError("no user_history")
        cache = FingerprintCache()
        fp = cache.get(state["user_id"])
        if fp is None:
            fp = build_behavioural_fingerprint.invoke({"user_history": history})
            cache.set(state["user_id"], fp)
        state = {**state, "fingerprint": fp}
        return _trace(state, "build_fingerprint", t0, f"style={fp.emotional_style}")
    except Exception as exc:
        logger.warning("build_fingerprint failed: %s", exc)
        state = append_error(state, f"build_fingerprint: {exc}")
        return _trace(state, "build_fingerprint", t0, "fallback fingerprint", "fallback")


def detect_region(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.region import detect_nigerian_region
        history = state.get("user_history")
        if history is None:
            raise ValueError("no user_history")
        region = detect_nigerian_region.invoke({"user_history": history})
        state = {**state, "region_profile": region}
        return _trace(state, "detect_region", t0, f"region={region.region}")
    except Exception as exc:
        logger.warning("detect_region failed: %s", exc)
        from naijareview.schemas.user import RegionProfile
        uid = state.get("user_id") or "cold_start"
        region = RegionProfile(user_id=uid, region="Unknown", confidence=0.0, signals=[])
        state = append_error({**state, "region_profile": region}, f"detect_region: {exc}")
        return _trace(state, "detect_region", t0, "fallback: Unknown", "fallback")


def bootstrap_fingerprint(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.skills.fingerprinting import FingerprintBuilder
        persona = state.get("cold_start_persona")
        if persona is None:
            raise ValueError("no cold_start_persona")

        builder = FingerprintBuilder(cache=object(), episodic=object())
        fp = builder.build_from_persona(persona)
        state = {**state, "fingerprint": fp}
        return _trace(state, "bootstrap_fingerprint", t0, "fingerprint bootstrapped from persona")
    except Exception as exc:
        logger.warning("bootstrap_fingerprint failed: %s", exc)
        state = append_error(state, f"bootstrap_fingerprint: {exc}")
        return _trace(state, "bootstrap_fingerprint", t0, "fallback fingerprint", "error")


def _llm_fallback_candidates(query: str, fp, persona, naija: bool) -> list:
    """Generate plausible Nigerian Item objects via LLM when FAISS is unavailable."""
    from naijareview.schemas.item import Item
    import re, json as _json

    fp_summary = ""
    if fp and fp.topic_focus:
        fp_summary = f"User likes: {', '.join(fp.topic_focus[:4])}."
    elif persona and persona.food_preference:
        fp_summary = f"User prefers: {persona.food_preference}."

    register = "casual Naija tone" if naija else "friendly English"
    prompt = (
        f"You are a Nigerian business recommendation engine.\n"
        f"Query: {query}\n"
        f"{fp_summary}\n"
        f"Generate 5 realistic Nigerian business recommendations relevant to the query.\n"
        f"Use {register} for descriptions.\n"
        f"Return ONLY valid JSON with this exact structure:\n"
        '{"items": [{"item_id": "llm_1", "name": "...", "category": "...", '
        '"description": "...", "avg_rating": 4.2, "review_count": 150}]}'
    )
    try:
        raw = _router.call_with_retry("utility", prompt, max_tokens=600)
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        data = _json.loads(m.group()) if m else _json.loads(cleaned)
        items = []
        for i, it in enumerate(data.get("items", [])[:8]):
            items.append(Item(
                item_id=it.get("item_id", f"llm_{i+1}"),
                name=it.get("name", "Unknown"),
                category=it.get("category", "General"),
                description=it.get("description"),
                avg_rating=float(it.get("avg_rating", 4.0)),
                review_count=int(it.get("review_count", 50)),
            ))
        return items
    except Exception as llm_exc:
        logger.warning("LLM fallback candidate generation failed: %s", llm_exc)
        return []


def retrieve_candidates(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    fp = state.get("fingerprint")
    persona = state.get("cold_start_persona")
    query = state.get("context_query", "")
    naija = state.get("naija_vibe_mode", False)

    try:
        from naijareview.tools.retrieval import retrieve_candidates_hybrid
        candidates = retrieve_candidates_hybrid.invoke({
            "query": query,
            "fingerprint": fp,
            "cold_start_persona": persona,
            "top_k": 20,
        })
        if candidates:
            state = {**state, "candidate_pool": candidates}
            return _trace(state, "retrieve_candidates", t0, f"{len(candidates)} candidates")
        # Empty result — fall through to LLM fallback
        logger.warning("retrieve_candidates: hybrid returned 0 results, trying LLM fallback")
    except Exception as exc:
        logger.warning("retrieve_candidates failed: %s — trying LLM fallback", exc)
        state = append_error(state, f"retrieve_candidates: {exc}")

    # LLM fallback: generate candidates directly when FAISS/BM25 unavailable
    fallback = _llm_fallback_candidates(query, fp, persona, naija)
    if fallback:
        state = {**state, "candidate_pool": fallback}
        return _trace(state, "retrieve_candidates", t0, f"LLM fallback: {len(fallback)} candidates", "fallback")

    state = {**state, "candidate_pool": []}
    return _trace(state, "retrieve_candidates", t0, "retrieval failed — no candidates", "error")


def rerank(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.reasoning import rerank_candidates
        candidates = state.get("candidate_pool", [])
        fp = state.get("fingerprint")
        query = state.get("context_query", "")

        if not candidates:
            raise ValueError("no candidates")

        ranked = rerank_candidates.invoke({
            "candidates": candidates,
            "fingerprint": fp,
            "context_query": query,
        })
        state = {**state, "reranked_candidates": ranked}
        return _trace(state, "rerank", t0, f"{len(ranked)} ranked items")
    except Exception as exc:
        logger.warning("rerank failed: %s", exc)
        # Fall back to original order with default scores
        from naijareview.schemas.item import RankedItem
        n = len(state.get("candidate_pool", []))
        ranked = [
            RankedItem(item=c, rank=i + 1, alignment_score=round((n - i) / max(n, 1), 4), reasoning_snippet="Default order.")
            for i, c in enumerate(state.get("candidate_pool", []))
        ]
        state = append_error({**state, "reranked_candidates": ranked}, f"rerank: {exc}")
        return _trace(state, "rerank", t0, "fallback: default order", "fallback")


def run_diversity_check(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.diversity import diversity_check
        from naijareview.config import settings
        ranked = state.get("reranked_candidates", [])
        if not ranked:
            raise ValueError("no reranked candidates")

        result, score = diversity_check.invoke({
            "ranked_items": ranked,
            "min_diversity": settings.min_diversity_score,
        })
        state = {**state, "reranked_candidates": result, "diversity_score": score}
        return _trace(state, "run_diversity_check", t0, f"diversity={score:.3f}")
    except Exception as exc:
        logger.warning("diversity_check failed: %s", exc)
        state = append_error({**state, "diversity_score": 0.0}, f"diversity_check: {exc}")
        return _trace(state, "run_diversity_check", t0, "diversity check skipped", "fallback")


def apply_taxonomy_batch(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        from naijareview.tools.taxonomy import apply_nigerian_taxonomy
        from naijareview.schemas.item import RankedItem
        ranked = state.get("reranked_candidates", [])
        enriched = []
        for ri in ranked:
            enriched_item = apply_nigerian_taxonomy.invoke({"item": ri.item})
            enriched.append(RankedItem(
                item=enriched_item,
                rank=ri.rank,
                alignment_score=ri.alignment_score,
                reasoning_snippet=ri.reasoning_snippet,
            ))
        state = {**state, "reranked_candidates": enriched}
        return _trace(state, "apply_taxonomy_batch", t0, f"{len(enriched)} items taxonomy-mapped")
    except Exception as exc:
        logger.warning("apply_taxonomy_batch failed: %s", exc)
        state = append_error(state, f"apply_taxonomy_batch: {exc}")
        return _trace(state, "apply_taxonomy_batch", t0, "taxonomy batch skipped", "fallback")


def generate_explanations(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        ranked = state.get("reranked_candidates", [])
        top5 = ranked[:5]
        fp = state.get("fingerprint")
        naija = state.get("naija_vibe_mode", False)
        region = state.get("region_profile")
        region_name = region.region if region else "Unknown"

        if not top5:
            raise ValueError("no candidates")

        if fp is not None:
            topic_str = ", ".join(fp.topic_focus) if fp.topic_focus else "general"
            fp_summary = (
                f"Likes: {topic_str}. Style: {fp.emotional_style}. "
                f"Generosity: {fp.generosity_score:.2f}. Slang index: {fp.naija_slang_index:.2f}."
            )
        else:
            fp_summary = f"Query: {state.get('context_query', 'Nigerian recommendations')}"

        items_block = "\n".join(
            f"[{ri.rank}] {ri.item.name} ({ri.item.nigerian_category or ri.item.category}) "
            f"score={ri.alignment_score:.2f} — {ri.reasoning_snippet}"
            for ri in top5
        )

        register = (
            "Naija register with Pidgin code-switching" if naija
            else "clear, friendly English"
        )

        prompt = (
            f"Write 2-3 sentence personalized explanations for these top {len(top5)} recommendations.\n"
            f"User profile: {fp_summary}\n"
            f"Region: {region_name}\n"
            f"Register: {register}\n\n"
            f"Items:\n{items_block}\n\n"
            f"Return ONLY valid JSON:\n"
            f'{{\"explanations\": [{{"rank": 1, "explanation": "..."}}]}}'
        )

        raw = _router.call_with_retry("generation", prompt)
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        data = json.loads(match.group()) if match else json.loads(cleaned)
        explanations: list[dict] = data.get("explanations", [])

        exp_map = {int(e.get("rank", 0)): str(e.get("explanation", "")) for e in explanations}

        from naijareview.schemas.item import Recommendation
        recs: list[Recommendation] = []
        for ri in top5:
            exp = exp_map.get(ri.rank, ri.reasoning_snippet)
            recs.append(Recommendation(
                item=ri.item,
                rank=ri.rank,
                explanation=exp,
                alignment_dimensions=fp.topic_focus[:3] if fp else [],
            ))

        state = {**state, "recommendations": recs}
        return _trace(state, "generate_explanations", t0, f"{len(recs)} explanations generated")
    except Exception as exc:
        logger.warning("generate_explanations failed: %s", exc)
        from naijareview.schemas.item import Recommendation
        recs = [
            Recommendation(
                item=ri.item,
                rank=ri.rank,
                explanation=ri.reasoning_snippet,
                alignment_dimensions=[],
            )
            for ri in state.get("reranked_candidates", [])[:5]
        ]
        state = append_error({**state, "recommendations": recs}, f"generate_explanations: {exc}")
        return _trace(state, "generate_explanations", t0, "fallback explanations", "fallback")


def compute_confidence(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        recs = state.get("recommendations", [])
        n = len(recs)
        alignment_factor = (
            sum(r.alignment_score for r in state.get("reranked_candidates", [])[:n]) / max(n, 1)
            if state.get("reranked_candidates") else 0.5
        )

        persona = state.get("cold_start_persona")
        if persona:
            filled = sum(1 for f in [
                persona.food_preference, persona.value_orientation,
                persona.atmosphere_preference, persona.budget_range,
                persona.frequency_of_dining_out,
            ] if f is not None)
            cold_start_coverage = filled / 5.0
        else:
            cold_start_coverage = 0.0

        diversity = state.get("diversity_score", 0.5)

        query = state.get("context_query", "")
        query_specificity = min(1.0, len(query.split()) / 10.0)

        confidence = (
            0.40 * alignment_factor
            + 0.25 * cold_start_coverage
            + 0.20 * diversity
            + 0.15 * query_specificity
        )
        confidence = round(max(0.0, min(1.0, confidence)), 4)
        state = {**state, "confidence": confidence}
        return _trace(state, "compute_confidence", t0, f"confidence={confidence:.3f}")
    except Exception as exc:
        logger.warning("compute_confidence failed: %s", exc)
        state = append_error({**state, "confidence": 0.5}, f"compute_confidence: {exc}")
        return _trace(state, "compute_confidence", t0, "fallback confidence=0.5", "fallback")


def confidence_gate(state: "TaskBState") -> Literal["finalise", "gen_clarifying_question"]:
    """Conditional edge: high confidence → finalise, low → clarifying question."""
    from naijareview.config import settings
    conf = state.get("confidence", 0.5)
    follow_ups = state.get("follow_up_turn_count", 0)
    if conf >= settings.task_b_confidence_threshold or follow_ups >= 1:
        return "finalise"
    return "gen_clarifying_question"


def finalise(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    state = {**state, "reasoning": f"Top recommendations based on user preferences and query: {state.get('context_query', '')}"}
    return _trace(state, "finalise", t0, f"{len(state.get('recommendations', []))} recommendations")


def gen_clarifying_question(state: "TaskBState") -> "TaskBState":
    t0 = _ts()
    try:
        query = state.get("context_query", "")
        recs = state.get("recommendations", [])
        categories = list({r.item.category for r in recs})[:3]
        naija = state.get("naija_vibe_mode", False)

        cats_str = ", ".join(categories) if categories else "various options"
        prompt = (
            f"A user asked: '{query}'. You found {len(recs)} recommendations across {cats_str}. "
            f"Ask ONE short clarifying question to refine the recommendations. "
            f"{'Use casual Naija tone.' if naija else 'Be friendly and concise.'} "
            f"Return ONLY valid JSON: {{\"question\": \"...\"}}"
        )
        raw = _router.call_with_retry("utility", prompt, max_tokens=100)
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        data = json.loads(match.group()) if match else json.loads(cleaned)
        question = str(data.get("question", "Could you tell me more about what you're looking for?"))

        follow_ups = state.get("follow_up_turn_count", 0) + 1
        state = {**state, "follow_up_question": question, "follow_up_turn_count": follow_ups}
        return _trace(state, "gen_clarifying_question", t0, "clarifying question generated")
    except Exception as exc:
        logger.warning("gen_clarifying_question failed: %s", exc)
        state = append_error(
            {**state, "follow_up_question": "Could you tell me more about what you're looking for?",
             "follow_up_turn_count": state.get("follow_up_turn_count", 0) + 1},
            f"gen_clarifying_question: {exc}",
        )
        return _trace(state, "gen_clarifying_question", t0, "fallback question", "fallback")
