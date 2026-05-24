"""Task A node implementations.

Owner: Testimony
See §6.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Literal

from naijareview.agents.nodes.shared import append_error
from naijareview.llm.router import LLMRouter
from naijareview.skills.context_assembly import ContextWindowAssembler
from naijareview.skills.persona_authoring import PersonaAuthor
from naijareview.skills.regeneration import RegenerationStrategist
from naijareview.agents.task_a import TaskAState

logger = logging.getLogger(__name__)
_router = LLMRouter()
_persona_author = PersonaAuthor()
_assembler = ContextWindowAssembler()
_regen = RegenerationStrategist()


def _ts() -> float:
    return time.time()


def _trace(state: "TaskAState", node: str, started: float, summary: str, status: str = "ok") -> "TaskAState":
    entry = {
        "node": node,
        "started_at": started,
        "duration_ms": round((time.time() - started) * 1000, 1),
        "status": status,
        "summary": summary,
    }
    return {**state, "trace": [*state.get("trace", []), entry]}


# ── Nodes ─────────────────────────────────────────────────────────────────────

def load_history(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.memory import load_user_history
        history = load_user_history.invoke({"user_id": state["user_id"]})
        state = {**state, "user_history": history}
        return _trace(state, "load_history", t0, f"{history.review_count} reviews loaded")
    except Exception as exc:
        logger.warning("load_history failed: %s", exc)
        state = append_error(state, f"load_history: {exc}")
        return _trace(state, "load_history", t0, "fallback: empty history", "error")


def build_fingerprint(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.fingerprint import build_behavioural_fingerprint
        from naijareview.memory.semantic import FingerprintCache
        history = state.get("user_history")
        if history is None:
            raise ValueError("no user_history in state")
        cache = FingerprintCache()
        fp = cache.get(state["user_id"])
        if fp is None:
            fp = build_behavioural_fingerprint.invoke({"user_history": history})
            cache.set(state["user_id"], fp)
        state = {**state, "fingerprint": fp}
        return _trace(state, "build_fingerprint", t0, f"generosity={fp.generosity_score:.2f} style={fp.emotional_style}")
    except Exception as exc:
        logger.warning("build_fingerprint failed: %s", exc)
        state = append_error(state, f"build_fingerprint: {exc}")
        return _trace(state, "build_fingerprint", t0, "fallback fingerprint", "fallback")


def detect_region(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.region import detect_nigerian_region
        history = state.get("user_history")
        if history is None:
            raise ValueError("no user_history")
        region = detect_nigerian_region.invoke({"user_history": history})
        state = {**state, "region_profile": region}
        return _trace(state, "detect_region", t0, f"region={region.region} conf={region.confidence:.2f}")
    except Exception as exc:
        logger.warning("detect_region failed: %s", exc)
        from naijareview.schemas.user import RegionProfile
        region = RegionProfile(user_id=state["user_id"], region="Unknown", confidence=0.0, signals=[])
        state = append_error({**state, "region_profile": region}, f"detect_region: {exc}")
        return _trace(state, "detect_region", t0, "fallback: Unknown region", "fallback")


def analyse_item(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.reasoning import analyse_item_for_user
        fp = state.get("fingerprint")
        item = state["item"]
        if fp is None:
            raise ValueError("no fingerprint")
        analysis = analyse_item_for_user.invoke({"item": item, "fingerprint": fp})
        state = {**state, "item_analysis": analysis}
        return _trace(state, "analyse_item", t0, f"sentiment={analysis.get('inferred_sentiment')}")
    except Exception as exc:
        logger.warning("analyse_item failed: %s", exc)
        state = append_error({**state, "item_analysis": {}}, f"analyse_item: {exc}")
        return _trace(state, "analyse_item", t0, "fallback item analysis", "fallback")


def apply_taxonomy(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.taxonomy import apply_nigerian_taxonomy
        item = state["item"]
        enriched = apply_nigerian_taxonomy.invoke({"item": item})
        state = {**state, "item": enriched}
        return _trace(state, "apply_taxonomy", t0, f"nigerian_category={enriched.nigerian_category}")
    except Exception as exc:
        logger.warning("apply_taxonomy failed: %s", exc)
        state = append_error(state, f"apply_taxonomy: {exc}")
        return _trace(state, "apply_taxonomy", t0, "taxonomy skipped", "fallback")


def fetch_few_shots(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.persona import fetch_few_shot_examples
        analysis = state.get("item_analysis") or {}
        region = state.get("region_profile")
        sentiment = analysis.get("inferred_sentiment", "neutral")
        sent_key: Literal["positive", "negative", "mixed"] = (
            "positive" if sentiment == "positive"
            else "negative" if sentiment == "negative"
            else "mixed"
        )
        region_name = region.region if region else "Unknown"
        item = state["item"]
        examples = fetch_few_shot_examples.invoke({
            "region": region_name,
            "sentiment": sent_key,
            "category": item.category,
            "k": 3,
        })
        state = {**state, "few_shot_examples": examples}
        return _trace(state, "fetch_few_shots", t0, f"{len(examples)} examples fetched")
    except Exception as exc:
        logger.warning("fetch_few_shots failed: %s", exc)
        state = append_error({**state, "few_shot_examples": []}, f"fetch_few_shots: {exc}")
        return _trace(state, "fetch_few_shots", t0, "fallback: no examples", "fallback")


def author_persona(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        fp = state.get("fingerprint")
        region = state.get("region_profile")
        item = state["item"]
        naija = state.get("naija_vibe_mode", False)
        retry = state.get("retry_count", 0)

        if fp is None or region is None:
            raise ValueError("missing fingerprint or region")

        intensity: Literal["natural", "amplified"] = (
            "amplified" if (naija and retry > 0) else "natural"
        )
        block = _persona_author.author(fp, region, item, intensity)
        state = {**state, "persona_block": block}
        return _trace(state, "author_persona", t0, f"intensity={intensity}")
    except Exception as exc:
        logger.warning("author_persona failed: %s", exc)
        state = append_error(
            {**state, "persona_block": "Write a genuine, personal review."},
            f"author_persona: {exc}",
        )
        return _trace(state, "author_persona", t0, "fallback persona block", "fallback")


def assemble_prompt(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        fp = state.get("fingerprint")
        region = state.get("region_profile")
        item = state["item"]
        few_shots = state.get("few_shot_examples", [])
        persona_block = state.get("persona_block", "")
        naija = state.get("naija_vibe_mode", False)
        regen_hint = state.get("regeneration_hint")
        analysis = state.get("item_analysis")

        if fp is None or region is None:
            raise ValueError("missing fingerprint or region")

        prompt = _assembler.assemble_task_a(
            fingerprint=fp,
            region=region,
            item=item,
            few_shots=few_shots,
            persona_block=persona_block,
            naija_vibe_mode=naija,
            item_analysis=analysis,
            regen_hint=regen_hint,
        )
        state = {**state, "assembled_prompt": prompt}
        return _trace(state, "assemble_prompt", t0, f"prompt_len={len(prompt)}")
    except Exception as exc:
        logger.warning("assemble_prompt failed: %s", exc)
        item = state["item"]
        fallback = (
            f"Write a detailed, authentic review for '{item.name}' (category: {item.category}). "
            f"Based on the review you write, infer an appropriate star rating from 1 to 5. "
            f"Return only valid JSON with no markdown: {{\"review\": \"...\", \"rating\": <1-5>}}"
        )
        state = append_error({**state, "assembled_prompt": fallback}, f"assemble_prompt: {exc}")
        return _trace(state, "assemble_prompt", t0, "fallback prompt", "fallback")


def _parse_draft(raw: str) -> tuple[str, float]:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    data = json.loads(match.group()) if match else json.loads(cleaned)
    review = str(data.get("review", "")).strip()
    rating = max(1.0, min(5.0, float(data.get("rating", 3.0))))
    return review, rating


def generate_draft(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    prompt = state.get("assembled_prompt", "")
    try:
        raw = _router.call_with_retry("generation", prompt)
        review, rating = _parse_draft(raw)

        # Empty response from Gemini Pro (thinking tokens exhausted) — retry with Flash
        if not review:
            logger.warning("generate_draft: generation tier returned empty, retrying with utility")
            raw = _router.call_with_retry("utility", prompt)
            review, rating = _parse_draft(raw)

        if not review:
            raise ValueError("both tiers returned empty review text")

        fp = state.get("fingerprint")
        min_words = max(50, fp.verbosity_word_range[0] if fp else 50)
        word_count = len(review.split())
        if word_count < min_words // 2:
            logger.warning("generate_draft: review too short (%d words), retrying with utility", word_count)
            raw = _router.call_with_retry("utility", prompt)
            short_review, short_rating = _parse_draft(raw)
            if len(short_review.split()) > word_count:
                review, rating = short_review, short_rating

        state = {**state, "draft_review": review, "draft_rating": rating}
        return _trace(state, "generate_draft", t0, f"rating={rating:.1f} words={len(review.split())}")
    except Exception as exc:
        logger.warning("generate_draft failed: %s", exc)
        state = append_error(
            {**state, "draft_review": "", "draft_rating": None},
            f"generate_draft: {exc}",
        )
        return _trace(state, "generate_draft", t0, "generation failed", "error")


def vibe_check(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        from naijareview.tools.vibe import run_naija_vibe_check
        review = state.get("draft_review", "")
        fp = state.get("fingerprint")
        item = state["item"]
        naija = state.get("naija_vibe_mode", False)
        mode = "active" if naija else "passive"

        if not review or fp is None:
            raise ValueError("missing draft or fingerprint")

        score = run_naija_vibe_check.invoke({
            "review_text": review,
            "target_fingerprint": fp,
            "item": item,
            "mode": mode,
        })
        state = {**state, "vibe_score": score}
        return _trace(state, "vibe_check", t0, f"abeg={score.abeg_score:.3f} mode={mode}")
    except Exception as exc:
        logger.warning("vibe_check failed: %s", exc)
        from naijareview.schemas.vibe import VibeScore
        fallback = VibeScore(
            cultural_authenticity=0.5, cultural_accuracy=0.5,
            persona_consistency=0.5, abeg_score=0.5,
            breakdown={"error": str(exc)}, scored_in_mode="passive",
        )
        state = append_error({**state, "vibe_score": fallback}, f"vibe_check: {exc}")
        return _trace(state, "vibe_check", t0, "vibe check failed — fallback score", "error")


def decide_after_vibe_check(state: "TaskAState") -> Literal["plan_regeneration", "finalise_output"]:
    """Conditional edge: route to regen or finalise."""
    from naijareview.config import settings
    naija = state.get("naija_vibe_mode", False)
    score = state.get("vibe_score")
    retry = state.get("retry_count", 0)

    if (
        naija
        and score is not None
        and score.abeg_score < settings.vibe_regen_threshold
        and retry < settings.vibe_max_retries
    ):
        return "plan_regeneration"
    return "finalise_output"


def plan_regeneration(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        score = state["vibe_score"]
        few_shots = state.get("few_shot_examples", [])
        region = state.get("region_profile")
        from naijareview.schemas.user import RegionProfile
        region_obj = region or RegionProfile(
            user_id=state["user_id"], region="Unknown", confidence=0.0, signals=[]
        )
        plan = _regen.plan(vibe_score=score, current_few_shots=few_shots, region=region_obj)
        retry = state.get("retry_count", 0)
        state = {**state, "retry_count": retry + 1, "regeneration_hint": plan.prompt_addition}
        return _trace(state, "plan_regeneration", t0, f"retry={retry + 1} hint set")
    except Exception as exc:
        logger.warning("plan_regeneration failed: %s", exc)
        state = append_error(
            {**state, "retry_count": state.get("retry_count", 0) + 1, "regeneration_hint": None},
            f"plan_regeneration: {exc}",
        )
        return _trace(state, "plan_regeneration", t0, "regen plan failed", "error")


def finalise_output(state: "TaskAState") -> "TaskAState":
    t0 = _ts()
    try:
        review = state.get("draft_review", "") or ""
        rating = state.get("draft_rating")  # None means LLM failed — do not default yet
        score = state.get("vibe_score")
        fp = state.get("fingerprint")
        retry = state.get("retry_count", 0)
        naija = state.get("naija_vibe_mode", False)
        region = state.get("region_profile")

        # ── LLM-driven Nigerian cultural enrichment (naija mode only) ───────
        # PhraseLibrary + CodeSwitcher provide reference examples/loanwords;
        # the LLM does all actual language transformation for naturalness.
        if naija and review:
            try:
                from naijareview.nigerian_lang.phrase_library import PhraseLibrary
                from naijareview.nigerian_lang.code_switching import _LOANWORDS

                region_name = region.region if region else "Unknown"
                slang_idx = fp.naija_slang_index if fp else 0.3
                _r = rating if rating is not None else 3.0
                sentiment = "positive" if _r >= 3.5 else "negative"
                intensity_label = "heavy" if slang_idx > 0.6 else ("amplified" if slang_idx > 0.3 else "natural")
                item = state.get("item")
                category = item.category if item else "general"

                lib = PhraseLibrary()
                example_phrases = lib.get_phrases(
                    region=region_name, sentiment=sentiment,
                    category=category, intensity=intensity_label, k=3,
                )
                vocab = _LOANWORDS.get(region_name, _LOANWORDS["Unknown"])
                loanwords = vocab.get("openers", []) + vocab.get("affirmations", []) + vocab.get("closers", [])

                phrase_block = "\n".join(f'- "{p}"' for p in example_phrases) if example_phrases else "(none)"
                loanword_block = ", ".join(loanwords[:8]) if loanwords else "(none)"

                polish_prompt = (
                    f"You are a Nigerian review editor. Rewrite the draft review below so it "
                    f"sounds authentically Nigerian — natural {intensity_label} Pidgin, matching "
                    f"the user's slang intensity ({slang_idx:.2f}/1.0). "
                    f"Use the reference phrases and loanwords as style guides but do NOT copy "
                    f"them verbatim. Keep the original facts, sentiment, and rating intact. "
                    f"Minimum 60 words.\n\n"
                    f"REGION: {region_name}\n"
                    f"REFERENCE PHRASES (style guide):\n{phrase_block}\n"
                    f"REGIONAL LOANWORDS: {loanword_block}\n\n"
                    f"DRAFT REVIEW:\n{review}\n\n"
                    f"Return ONLY valid JSON with no markdown. "
                    f"Assign a star rating (1.0–5.0) that honestly reflects the sentiment "
                    f"of the rewritten review — do not default to 3.0. "
                    f'Format: {{\"review\": \"...\", \"rating\": <1.0-5.0>}}'
                )
                raw = _router.call_with_retry("utility", polish_prompt)
                cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    polished = str(data.get("review", "")).strip()
                    if polished and len(polished.split()) >= 20:
                        review = polished
                        raw_rating = data.get("rating")
                        if raw_rating is not None:
                            rating = max(1.0, min(5.0, float(raw_rating)))
            except Exception as pe:
                logger.warning("naija cultural enrichment failed: %s", pe)

        # ── Rating inference fallback ─────────────────────────────────────
        # If no rating was predicted (cold-start LLM failure), infer from review text
        if rating is None and review:
            try:
                infer_prompt = (
                    f"Read this review and respond with ONLY a JSON object: "
                    f'{{\"rating\": <1.0-5.0>}}\n'
                    f"Base the rating purely on the sentiment expressed. "
                    f"Do not default to 3.0 — read the text carefully.\n\n"
                    f"REVIEW:\n{review}"
                )
                raw_r = _router.call_with_retry("utility", infer_prompt)
                cleaned_r = re.sub(r"```(?:json)?", "", raw_r).strip().rstrip("`").strip()
                m_r = re.search(r"\{.*?\}", cleaned_r, re.DOTALL)
                if m_r:
                    rating = max(1.0, min(5.0, float(json.loads(m_r.group()).get("rating", 3.0))))
            except Exception:
                rating = 3.0  # last resort only
        if rating is None:
            rating = 3.0

        # ── Confidence ────────────────────────────────────────────────────
        persona_consistency = score.persona_consistency if score else 0.5
        cultural_authenticity = score.cultural_authenticity if score else 0.5
        retry_penalty = retry * 0.1
        region_conf = region.confidence if region else 0.0

        confidence = (
            0.40 * persona_consistency
            + 0.35 * cultural_authenticity
            + 0.15 * (1.0 - retry_penalty)
            + 0.10 * region_conf
        )
        confidence = round(max(0.0, min(1.0, confidence)), 4)

        topics = fp.topic_focus[:3] if fp else []
        fingerprint_match = f"Matched on: {', '.join(topics)}" if topics else "General match"

        state = {
            **state,
            "final_review": review,
            "final_rating": rating,
            "confidence": confidence,
            "fingerprint_match_summary": fingerprint_match,
            "style_notes": f"emotional_style={fp.emotional_style if fp else 'unknown'}",
        }
        return _trace(state, "finalise_output", t0, f"confidence={confidence:.3f}")
    except Exception as exc:
        logger.warning("finalise_output failed: %s", exc)
        state = append_error(state, f"finalise_output: {exc}")
        return _trace(state, "finalise_output", t0, "finalise failed", "error")
