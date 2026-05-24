"""Startup warmup — pre-loads all heavy singletons before the API serves traffic.

Called from the FastAPI lifespan context manager in main.py.
All singletons are stored here and imported by routes / tools.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── Singleton registry ────────────────────────────────────────────────────────

_registry: dict[str, Any] = {
    "embedding_provider": None,
    "item_index": None,
    "task_a_graph": None,
    "task_b_graph": None,
    "chroma_ok": False,
    "faiss_ok": False,
    "bm25_ok": False,
    "warmup_errors": [],
    "ready": False,
}


def get_task_a_graph():
    return _registry["task_a_graph"]


def get_task_b_graph():
    return _registry["task_b_graph"]


def get_embedding_provider():
    return _registry["embedding_provider"]


def get_item_index():
    return _registry["item_index"]


def get_status() -> dict:
    return {
        "embedding": "ok" if _registry["embedding_provider"] is not None else "not_ready",
        "faiss": "ok" if _registry["faiss_ok"] else "not_ready",
        "bm25": "ok" if _registry["bm25_ok"] else "not_ready",
        "chroma": "ok" if _registry["chroma_ok"] else "not_ready",
        "task_a_graph": "ok" if _registry["task_a_graph"] is not None else "not_ready",
        "task_b_graph": "ok" if _registry["task_b_graph"] is not None else "not_ready",
        "errors": _registry["warmup_errors"],
        "ready": _registry["ready"],
    }


# ── Warmup steps ──────────────────────────────────────────────────────────────

def _step(name: str, fn):
    t0 = time.perf_counter()
    try:
        result = fn()
        ms = (time.perf_counter() - t0) * 1000
        logger.info("startup [ok] %-30s %.0fms", name, ms)
        return result
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000
        logger.error("startup [fail] %-28s %.0fms  %s", name, ms, exc)
        _registry["warmup_errors"].append(f"{name}: {exc}")
        return None


def warm_up() -> None:
    """Load all heavy components synchronously. Called in a thread from lifespan."""
    logger.info("=== NaijaReview API warmup starting ===")
    t_total = time.perf_counter()

    from naijareview.config import settings

    # ── 1. Embedding model ────────────────────────────────────────────────────
    def load_embedding():
        from naijareview.memory.embedding import EmbeddingProvider
        p = EmbeddingProvider()
        _ = p.dim()  # forces model load
        return p

    provider = _step("embedding_model (bge-base-en-v1.5)", load_embedding)
    _registry["embedding_provider"] = provider

    # ── 2. FAISS item index ───────────────────────────────────────────────────
    def load_faiss():
        from naijareview.memory.item_index import ItemIndex
        idx = ItemIndex(
            index_path=settings.faiss_index_path,
            embed_provider=_registry["embedding_provider"],
        )
        _registry["faiss_ok"] = True
        return idx

    item_index = _step("faiss_item_index", load_faiss)
    _registry["item_index"] = item_index

    # ── 3. BM25 index ─────────────────────────────────────────────────────────
    def load_bm25():
        from naijareview.tools.retrieval import BM25Index
        idx = BM25Index(
            metadata_path=settings.faiss_index_path.with_suffix(".json"),
        )
        # _load() called in __init__ if file exists; verify corpus loaded
        if not idx._bm25:
            raise RuntimeError("BM25 corpus empty — metadata file missing or empty")
        _registry["bm25_ok"] = True

    _step("bm25_index", load_bm25)

    # ── 4. ChromaDB Railway heartbeat ─────────────────────────────────────────
    def ping_chroma():
        import chromadb
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            ssl=settings.chroma_ssl,
            headers={"Authorization": f"Bearer {settings.chroma_auth_token}"},
        )
        client.heartbeat()
        _registry["chroma_ok"] = True

    _step("chromadb_heartbeat", ping_chroma)

    # ── 5. Compile Task A graph ───────────────────────────────────────────────
    def compile_task_a():
        from naijareview.agents.task_a import build_task_a_graph
        return build_task_a_graph()

    _registry["task_a_graph"] = _step("task_a_graph_compile", compile_task_a)

    # ── 6. Compile Task B graph ───────────────────────────────────────────────
    def compile_task_b():
        from naijareview.agents.task_b import build_task_b_graph
        return build_task_b_graph()

    _registry["task_b_graph"] = _step("task_b_graph_compile", compile_task_b)

    # ── Done ──────────────────────────────────────────────────────────────────
    total_ms = (time.perf_counter() - t_total) * 1000
    _registry["ready"] = len(_registry["warmup_errors"]) == 0
    status = "READY" if _registry["ready"] else f"DEGRADED ({len(_registry['warmup_errors'])} errors)"
    logger.info("=== NaijaReview API warmup %s in %.0fms ===", status, total_ms)
