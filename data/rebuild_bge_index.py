"""Rebuild FAISS item index using a BGE model.

Default: BAAI/bge-small-en-v1.5  (384d, 33M params — fast on CPU, ~2 min)
Option:  BAAI/bge-m3             (1024d, 570M params — needs GPU, ~7h on CPU)

Saves to:
    data/processed/faiss_index_bge       (binary index)
    data/processed/faiss_index_bge.json  (metadata sidecar, same format as MiniLM)

Usage (from repo root, venv activated):
    # CPU-fast default
    venv/bin/python data/rebuild_bge_index.py

    # Full BGE-M3 — only use if you have a CUDA GPU
    venv/bin/python data/rebuild_bge_index.py --model BAAI/bge-m3

Comparison:
    MiniLM (384d)  → data/processed/faiss_index       ~2 min CPU
    BGE-small (384d) → data/processed/faiss_index_bge  ~2 min CPU  ← default here
    BGE-M3 (1024d) → data/processed/faiss_index_bge   ~2 min GPU / ~7h CPU
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ITEMS_PATH = ROOT / "data" / "processed" / "items.jsonl"
OUT_INDEX  = ROOT / "data" / "processed" / "faiss_index_bge"
OUT_META   = ROOT / "data" / "processed" / "faiss_index_bge.json"

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
BATCH_SIZE    = 128   # small model is fast — bigger batch = fewer Python loops


def _build_text(item: dict) -> str:
    parts = [
        item.get("name", ""),
        item.get("nigerian_category") or item.get("category", ""),
        item.get("description") or "",
    ]
    return " | ".join(p.strip() for p in parts if p.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"HuggingFace model name (default: {DEFAULT_MODEL})")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = ap.parse_args()

    model_name = args.model
    batch_size = args.batch_size

    print(f"Model:      {model_name}")
    print(f"Batch size: {batch_size}")
    print(f"Items:      {ITEMS_PATH}")
    print(f"Output:     {OUT_INDEX}\n")

    # ── Load items ──────────────────────────────────────────────────────────
    print("Loading items ...")
    items: list[dict] = []
    with ITEMS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    print(f"  {len(items):,} items loaded")

    texts = [_build_text(item) for item in items]

    # ── Load model ──────────────────────────────────────────────────────────
    print(f"\nLoading {model_name} ...")
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    dim = model.get_embedding_dimension() if hasattr(model, "get_embedding_dimension") else model.get_sentence_embedding_dimension()
    print(f"  Loaded in {time.time() - t0:.1f}s  |  dim={dim}")

    # ── Encode ──────────────────────────────────────────────────────────────
    print(f"\nEncoding {len(texts):,} texts ...")
    t1 = time.time()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,   # cosine via inner product
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    elapsed = time.time() - t1
    print(f"  Done in {elapsed:.1f}s  ({len(texts)/elapsed:.0f} items/s)")

    vecs = embeddings.astype(np.float32)

    # ── Build FAISS IndexFlatIP ─────────────────────────────────────────────
    print("\nBuilding FAISS IndexFlatIP ...")
    index = faiss.IndexFlatIP(dim)
    index.add(vecs)
    print(f"  {index.ntotal:,} vectors  |  dim={index.d}")

    # ── Save ────────────────────────────────────────────────────────────────
    print(f"\nSaving index    → {OUT_INDEX}")
    faiss.write_index(index, str(OUT_INDEX))

    print(f"Saving metadata → {OUT_META}")
    with OUT_META.open("w") as f:
        json.dump(items, f, indent=2)

    size_mb = OUT_INDEX.stat().st_size / 1_048_576
    print(f"\n✓  BGE index ready")
    print(f"   Model:   {model_name}")
    print(f"   Vectors: {index.ntotal:,}  |  dim={dim}  |  {size_mb:.1f} MB")
    print(f"   Index:   {OUT_INDEX}")
    print(f"   Meta:    {OUT_META}")
    print(f"\nTest it:  venv/bin/python data/test_faiss.py --bge")
    print(f"Compare:  venv/bin/python data/test_faiss.py --both")


if __name__ == "__main__":
    main()
