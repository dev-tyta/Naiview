"""Quick smoke-test for the existing FAISS indexes.

Usage (from repo root, venv activated):
    python data/test_faiss.py                  # tests MiniLM index
    python data/test_faiss.py --bge            # tests BGE index (must be built first)
    python data/test_faiss.py --both           # side-by-side comparison

Output shows top-5 results per query with score, name, and category.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

INDEXES = {
    "minilm": {
        "index": ROOT / "data/processed/faiss_index",
        "meta":  ROOT / "data/processed/faiss_index.json",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dim":   384,
    },
    "bge": {
        "index": ROOT / "data/processed/faiss_index_bge",
        "meta":  ROOT / "data/processed/faiss_index_bge.json",
        "model": "BAAI/bge-small-en-v1.5",   # swap to bge-m3 if GPU available
        "dim":   384,
    },
}

QUERIES = [
    "Nigerian suya spot Kano street food",
    "jollof rice Lagos restaurant",
    "budget smartphone Nigeria",
    "Chinua Achebe African literature book",
    "nightlife bar lounge Lagos",
]


def load_index(cfg: dict) -> tuple:
    index = faiss.read_index(str(cfg["index"]))
    with open(cfg["meta"]) as f:
        meta = json.load(f)
    return index, meta


def get_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    print(f"  Loading {model_name} ...", end=" ", flush=True)
    t0 = time.time()
    m = SentenceTransformer(model_name)
    print(f"done ({time.time()-t0:.1f}s)")
    return m


def search(query: str, index, meta: list, model, top_k: int = 5) -> list[dict]:
    vec = model.encode([query], normalize_embeddings=True).astype(np.float32)
    scores, indices = index.search(vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        item = meta[int(idx)]
        results.append({
            "score": float(score),
            "name": item.get("name", "?"),
            "category": item.get("nigerian_category") or item.get("category", "?"),
            "domain": item.get("domain", "?"),
        })
    return results


def run_test(name: str, cfg: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  INDEX: {name.upper()}  |  model={cfg['model']}  |  dim={cfg['dim']}")
    print(f"{'='*60}")

    if not Path(cfg["index"]).exists():
        print(f"  ✗ Index not found at {cfg['index']}")
        print(f"    Run: python data/rebuild_bge_index.py")
        return

    index, meta = load_index(cfg)
    print(f"  Loaded: {index.ntotal:,} vectors  |  dim={index.d}")
    model = get_model(cfg["model"])

    for q in QUERIES:
        t0 = time.time()
        results = search(q, index, meta, model)
        elapsed_ms = (time.time() - t0) * 1000
        print(f"\n  Query: \"{q}\"  ({elapsed_ms:.0f}ms)")
        for i, r in enumerate(results, 1):
            print(f"    {i}. [{r['score']:.3f}] {r['name']}  —  {r['category']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bge", action="store_true", help="Test BGE index only")
    ap.add_argument("--both", action="store_true", help="Test both indexes")
    args = ap.parse_args()

    if args.both:
        run_test("minilm", INDEXES["minilm"])
        run_test("bge",    INDEXES["bge"])
    elif args.bge:
        run_test("bge", INDEXES["bge"])
    else:
        run_test("minilm", INDEXES["minilm"])


if __name__ == "__main__":
    main()
