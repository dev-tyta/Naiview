"""Admin routes — debugging, introspection, and eval results."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from naijareview.config import settings

router = APIRouter()

_RESULTS_DIR = Path("results/eval")


@router.get("/health")
async def admin_health() -> dict:
    """Detailed health check — component status."""
    return {
        "status": "ok",
        "service": "naijareview",
        "version": "0.1.0",
        "mode": "hackathon",
        "components": {
            "gemini_api": "not_checked",  # TODO: ping Gemini health endpoint
            "chromadb": "stub",
            "faiss": "stub",
            "fingerprint_cache": settings.cache_backend,
        },
    }


@router.get("/index-stats")
async def index_stats() -> dict:
    """Return Chroma + FAISS index counts and cache stats."""
    # TODO: query real backends when wired
    return {
        "chroma_collections": 0,
        "faiss_items": 0,
        "users_cached": 0,
        "cache_backend": settings.cache_backend,
        "cache_ttl_hours": settings.fingerprint_cache_ttl_hours,
    }


@router.post("/rebuild-fingerprint/{user_id}")
async def rebuild_fingerprint(user_id: str) -> dict:
    """Force recompute a user's behavioural fingerprint."""
    # TODO: call FingerprintBuilder.invalidate() then get_or_build()
    return {
        "user_id": user_id,
        "status": "not_implemented",
        "note": "Set GEMINI_API_KEY and wire ChromaDB to enable",
    }


@router.get("/results")
async def get_eval_results() -> dict:
    """Return the most-recent eval results for every variant found in results/eval/.

    Used by the website metrics dashboard and for paper cross-referencing.
    Aggregates all JSON files in results/eval/ and returns the latest run
    per (task, variant) combination.
    """
    if not _RESULTS_DIR.exists():
        raise HTTPException(status_code=404, detail="No eval results found — run tests/eval/harness.py first")

    # Collect all result JSON files
    json_files = sorted(_RESULTS_DIR.glob("*.json"), reverse=True)  # newest first
    if not json_files:
        raise HTTPException(status_code=404, detail="No result files in results/eval/")

    task_a: dict[str, dict] = {}
    task_b: dict[str, dict] = {}

    for jf in json_files:
        name = jf.stem  # e.g. 2026-05-24_1915_task_a_full
        try:
            data = json.loads(jf.read_text())
        except Exception:
            continue
        variant = data.get("variant", "unknown")
        if "task_a" in name and variant not in task_a:
            task_a[variant] = data.get("metrics", {})
            task_a[variant]["meta"] = data.get("meta", {})
            task_a[variant]["n"] = data.get("n", 0)
        elif "task_b" in name and variant not in task_b:
            task_b[variant] = data.get("metrics", {})
            task_b[variant]["meta"] = data.get("meta", {})
            task_b[variant]["n"] = data.get("n", 0)

    # Latest ablation CSV as raw text (for paper tooling)
    csv_files = sorted(_RESULTS_DIR.glob("*ablation_comparison.csv"), reverse=True)
    ablation_csv = csv_files[0].read_text() if csv_files else None

    # Latest markdown summary
    md_files = sorted(_RESULTS_DIR.glob("*summary.md"), reverse=True)
    summary_md = md_files[0].read_text() if md_files else None

    return {
        "task_a": task_a,
        "task_b": task_b,
        "ablation_csv": ablation_csv,
        "summary_md": summary_md,
        "result_files": [f.name for f in json_files],
    }


@router.get("/results/latest-summary")
async def get_latest_summary() -> dict:
    """Return only the latest markdown summary — lightweight endpoint for the website."""
    md_files = sorted(_RESULTS_DIR.glob("*summary.md"), reverse=True) if _RESULTS_DIR.exists() else []
    if not md_files:
        raise HTTPException(status_code=404, detail="No summary found — run eval first")
    return {"summary_md": md_files[0].read_text(), "file": md_files[0].name}


@router.get("/config")
async def admin_config() -> dict:
    """Return non-sensitive config values for debugging."""
    return {
        "api_debug": settings.api_debug,
        "cache_backend": settings.cache_backend,
        "generation_model": settings.gemini_generation_model,
        "utility_model": settings.gemini_utility_model,
        "vibe_regen_threshold": settings.vibe_regen_threshold,
        "vibe_max_retries": settings.vibe_max_retries,
        "retrieval_top_k": settings.retrieval_top_k,
        "bm25_weight": settings.bm25_weight,
        "semantic_weight": settings.semantic_weight,
        "task_b_confidence_threshold": settings.task_b_confidence_threshold,
        "min_diversity_score": settings.min_diversity_score,
        "min_history_for_fingerprint": settings.min_history_for_fingerprint,
    }
