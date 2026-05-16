"""Memory layer bootstrap script.

Builds two stores from processed data:

  1. FAISS item index  — semantic search for Task B retrieval
     Source : data/processed/items.jsonl  (enriched by enrich_items.py)
     Output : data/processed/faiss_index  (binary) + faiss_index.json (metadata)

  2. ChromaDB episodic memory  — user review history for Task A + Task B
     Source : data/processed/final_dataset.jsonl  (47K reviews)
     Output : data/chroma/  (persistent ChromaDB collection)

Both honour checkpoint files so interrupted runs can resume safely.

Run:
  python3 scripts/build_memory.py                   # build both
  python3 scripts/build_memory.py --faiss-only       # FAISS only
  python3 scripts/build_memory.py --chroma-only      # ChromaDB only
  python3 scripts/build_memory.py --dry-run          # stats, no writes
  python3 scripts/build_memory.py --max-users 200    # limit users (dev/test)
  python3 scripts/build_memory.py --reset            # wipe existing stores first
  python3 scripts/build_memory.py --batch-size 64    # ChromaDB insert batch size
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── .env loading (before naijareview imports) ─────────────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

PROCESSED = ROOT / "data" / "processed"
CHROMA_DIR = ROOT / "data" / "chroma"
FAISS_INDEX_PATH = PROCESSED / "faiss_index"
FAISS_META_PATH = PROCESSED / "faiss_index.json"
CHROMA_CHECKPOINT = PROCESSED / ".chroma_checkpoint.json"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    logger.info(msg)


# ── FAISS index builder ───────────────────────────────────────────────────────

def build_faiss_index(dry_run: bool, reset: bool) -> None:
    _log("=== FAISS index build ===")

    items_path = PROCESSED / "items.jsonl"
    if not items_path.exists():
        _log(f"ERROR: {items_path} not found — run build_final_dataset.py first")
        sys.exit(1)

    items: list[dict] = []
    with items_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    _log(f"Loaded {len(items)} items from {items_path.name}")

    # Show enrichment stats
    enriched = sum(1 for it in items if it.get("enriched"))
    has_topics = sum(1 for it in items if it.get("attributes", {}).get("top_topics"))
    _log(f"  enriched={enriched}/{len(items)}  with_topics={has_topics}/{len(items)}")

    if dry_run:
        _log("DRY RUN — FAISS index not written")
        return

    if reset and FAISS_INDEX_PATH.exists():
        FAISS_INDEX_PATH.unlink()
        _log("Reset: removed existing FAISS index")
    if reset and FAISS_META_PATH.exists():
        FAISS_META_PATH.unlink()
        _log("Reset: removed existing FAISS metadata")

    if FAISS_INDEX_PATH.exists() and FAISS_META_PATH.exists():
        _log("FAISS index already exists — skipping (use --reset to rebuild)")
        return

    _log("Building FAISS index (embedding model loading…)")
    t0 = time.time()

    from naijareview.memory.item_index import ItemIndex
    index = ItemIndex(
        index_path=FAISS_INDEX_PATH,
        metadata_path=FAISS_META_PATH,
    )
    index.build_index(items)

    elapsed = time.time() - t0
    _log(f"FAISS index built: {len(items)} items in {elapsed:.1f}s → {FAISS_INDEX_PATH}")

    # Smoke test
    results = index.search("Nigerian restaurant food Lagos", top_k=3)
    _log(f"  Smoke test (top 3 for 'Nigerian restaurant food Lagos'):")
    for r in results:
        _log(f"    {r.name} | {r.category} | ★{r.avg_rating}")


# ── ChromaDB loader ───────────────────────────────────────────────────────────

def _load_chroma_checkpoint() -> set[str]:
    if CHROMA_CHECKPOINT.exists():
        return set(json.loads(CHROMA_CHECKPOINT.read_text()).get("loaded_review_ids", []))
    return set()


def _save_chroma_checkpoint(loaded_ids: set[str]) -> None:
    CHROMA_CHECKPOINT.write_text(
        json.dumps({"loaded_review_ids": sorted(loaded_ids), "count": len(loaded_ids)}, indent=2)
    )


def build_chroma_memory(
    dry_run: bool,
    reset: bool,
    max_users: int | None,
    batch_size: int,
) -> None:
    _log("=== ChromaDB episodic memory build ===")

    dataset_path = PROCESSED / "final_dataset.jsonl"
    histories_path = PROCESSED / "user_histories.jsonl"

    if not dataset_path.exists():
        _log(f"ERROR: {dataset_path} not found — run build_final_dataset.py first")
        sys.exit(1)

    # ── 1. Load all reviews indexed by review_id ──────────────────────────────
    _log("Loading reviews from final_dataset.jsonl…")
    t_load = time.time()
    reviews_by_id: dict[str, dict] = {}
    reviews_by_user: dict[str, list[dict]] = defaultdict(list)

    with dataset_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            reviews_by_id[r["review_id"]] = r
            reviews_by_user[r["user_id"]].append(r)

    _log(f"  {len(reviews_by_id)} reviews | {len(reviews_by_user)} unique users ({time.time()-t_load:.1f}s)")

    # ── 2. Load user histories to determine eligible users ────────────────────
    eligible_users: list[str] = []
    if histories_path.exists():
        with histories_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    h = json.loads(line)
                    eligible_users.append(h["user_id"])
        _log(f"  {len(eligible_users)} users with ≥3 reviews from user_histories.jsonl")
    else:
        # Fall back to all users with ≥3 reviews
        eligible_users = [u for u, rs in reviews_by_user.items() if len(rs) >= 3]
        _log(f"  {len(eligible_users)} users with ≥3 reviews (no user_histories.jsonl)")

    if max_users:
        eligible_users = eligible_users[:max_users]
        _log(f"  Capped to {len(eligible_users)} users (--max-users)")

    total_reviews = sum(len(reviews_by_user[u]) for u in eligible_users)
    _log(f"  Total reviews to load: {total_reviews}")

    if dry_run:
        _log("DRY RUN — ChromaDB not written")
        return

    # ── 3. Init ChromaDB collection ───────────────────────────────────────────
    import chromadb

    if reset:
        import shutil
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR)
            _log("Reset: wiped ChromaDB directory")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection_name = "naijareview_reviews"
    try:
        collection = client.get_collection(collection_name)
        existing_count = collection.count()
        _log(f"  Existing collection '{collection_name}' with {existing_count} docs")
    except Exception:
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        existing_count = 0
        _log(f"  Created new collection '{collection_name}'")

    # ── 4. Load checkpoint ────────────────────────────────────────────────────
    already_loaded = _load_chroma_checkpoint()
    _log(f"  Checkpoint: {len(already_loaded)} reviews already loaded")

    # ── 5. Embed + insert in batches ──────────────────────────────────────────
    from naijareview.memory.embedding import EmbeddingProvider
    embedder = EmbeddingProvider()
    _log(f"  Embedding model ready (dim={embedder.dim()})")

    inserted = 0
    skipped = 0
    errors = 0
    t_start = time.time()

    for user_idx, user_id in enumerate(eligible_users):
        user_reviews = reviews_by_user.get(user_id, [])
        pending = [r for r in user_reviews if r["review_id"] not in already_loaded]

        if not pending:
            skipped += len(user_reviews)
            continue

        # Process in batches
        for batch_start in range(0, len(pending), batch_size):
            batch = pending[batch_start: batch_start + batch_size]
            texts = [r.get("text", "") for r in batch]

            try:
                embeddings = embedder.embed_batch(texts)

                ids = [r["review_id"] for r in batch]
                metadatas = [
                    {
                        "user_id": r["user_id"],
                        "item_id": r["item_id"],
                        "stars": int(r.get("stars", 3)),
                        "timestamp": _parse_date(r.get("date", "")),
                        "item_category": r.get("category", ""),
                    }
                    for r in batch
                ]

                collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                )

                for r in batch:
                    already_loaded.add(r["review_id"])
                inserted += len(batch)

            except Exception as exc:
                logger.warning("Batch insert failed (user=%s batch=%d): %s", user_id, batch_start, exc)
                errors += len(batch)

        # Checkpoint every 100 users
        if (user_idx + 1) % 100 == 0:
            _save_chroma_checkpoint(already_loaded)
            elapsed = time.time() - t_start
            rate = inserted / max(elapsed, 1)
            _log(
                f"  Progress: {user_idx+1}/{len(eligible_users)} users | "
                f"{inserted} inserted | {errors} errors | {rate:.0f} docs/s"
            )

    _save_chroma_checkpoint(already_loaded)

    elapsed = time.time() - t_start
    final_count = collection.count()
    _log(f"\nChromaDB load complete in {elapsed:.1f}s:")
    _log(f"  {inserted} reviews inserted | {skipped} skipped | {errors} errors")
    _log(f"  Collection now has {final_count} total documents")
    _log(f"  Checkpoint saved → {CHROMA_CHECKPOINT}")

    # Smoke test
    _log("  Smoke test — querying collection for sample user:")
    if eligible_users:
        sample_user = eligible_users[0]
        try:
            result = collection.get(
                where={"user_id": sample_user},
                include=["documents", "metadatas"],
                limit=2,
            )
            docs = result.get("documents") or []
            _log(f"    user={sample_user} → {len(docs)} docs found")
        except Exception as exc:
            _log(f"    Smoke test failed: {exc}")


def _parse_date(date_str: str) -> str:
    """Normalise date string to ISO format for ChromaDB metadata."""
    if not date_str:
        return datetime.now().isoformat()
    try:
        # Yelp format: "2019-05-27 19:45:52"
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").isoformat()
    except ValueError:
        try:
            return datetime.fromisoformat(date_str).isoformat()
        except ValueError:
            return datetime.now().isoformat()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS + ChromaDB memory layer")
    parser.add_argument("--faiss-only", action="store_true", help="Only build FAISS index")
    parser.add_argument("--chroma-only", action="store_true", help="Only load ChromaDB")
    parser.add_argument("--dry-run", action="store_true", help="Stats only — no writes")
    parser.add_argument("--reset", action="store_true", help="Wipe existing stores before building")
    parser.add_argument("--max-users", type=int, default=None, help="Cap users loaded into ChromaDB")
    parser.add_argument("--batch-size", type=int, default=64, help="ChromaDB insert batch size")
    args = parser.parse_args()

    if args.dry_run:
        _log("DRY RUN MODE — no files will be written")

    t_total = time.time()

    if not args.chroma_only:
        build_faiss_index(dry_run=args.dry_run, reset=args.reset)

    if not args.faiss_only:
        build_chroma_memory(
            dry_run=args.dry_run,
            reset=args.reset,
            max_users=args.max_users,
            batch_size=args.batch_size,
        )

    _log(f"\nTotal time: {time.time() - t_total:.1f}s")


if __name__ == "__main__":
    main()
