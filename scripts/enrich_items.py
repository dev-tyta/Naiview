"""LLM-powered item enrichment pipeline.

Reads raw items.jsonl (opaque IDs, keyword-inferred categories) and enriches
each item using Gemini Flash to produce:
  - name          : realistic business name inferred from review text
  - nigerian_category : verified/corrected against the taxonomy list
  - domain        : verified food | retail | hospitality | services | general
  - nigerian_mode_fit : whether this business type exists in Nigeria and benefits
                        from Nigerian cultural framing in Task A/B
  - description   : clean 1-2 sentence description for FAISS embedding
  - enrichment_confidence : model's confidence in the categorisation

Processes 5 items per LLM call → ~790 calls for 3,946 items (~8 min at 0.6s delay).
Checkpointed — safe to interrupt and resume.

Overwrites data/processed/items.jsonl with the enriched version.

Run:
  python3 scripts/enrich_items.py
  python3 scripts/enrich_items.py --dry-run
  python3 scripts/enrich_items.py --reset-checkpoint
  python3 scripts/enrich_items.py --batch-size 10   # faster, slightly lower quality
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

from dotenv import load_dotenv

load_dotenv()

# def _load_env() -> None:
#     env_path = ROOT / ".env"
#     if not env_path.exists():
#         return
#     for line in env_path.read_text().splitlines():
#         line = line.strip()
#         if line and not line.startswith("#") and "=" in line:
#             k, _, v = line.partition("=")
#             os.environ.setdefault(k.strip(), v.strip())


# _load_env()

PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
ITEMS_PATH = PROCESSED / "items.jsonl"
ENRICHED_PATH = PROCESSED / "items_enriched.jsonl"
CHECKPOINT = PROCESSED / ".enrich_checkpoint.json"

MODEL = "gemini-2.0-flash"
CALL_DELAY_S = 0.6
MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 5
REVIEW_SNIPPET_LEN = 280    # chars per review snippet shown to model
REVIEWS_PER_ITEM = 3        # how many review snippets per item
MAX_OUTPUT_TOKENS = 2500    # bumped from 2000 — extra fields (top_topics, sentiment_split)

# ── Nigerian category taxonomy ────────────────────────────────────────────────

NIGERIAN_CATEGORIES = [
    "Buka / Mama Put",
    "Suya Joint / Street Food",
    "Eateries (Mr Biggs-style)",
    "Pepper Soup Spot",
    "Beer Parlour",
    "Canteen / Bukateria",
    "Confectionery / Bakery",
    "Open Market Stall",
    "Guesthouse / Lodge",
    "Beauty / Salon",
    "General Restaurant",       # doesn't map cleanly to any Nigerian type
    "General Retail",
    "General Services",
    "General Hospitality",
]

DOMAINS = ["food", "retail", "hospitality", "services", "general"]

NIGERIAN_FIT_GUIDE = """
nigerian_mode_fit should be TRUE when:
- The business type commonly exists across Nigerian cities
- Nigerian cultural framing (food names, Pidgin, regional references) enriches the review
Examples: restaurants, fast food, salons, markets, hotels, pharmacies, gyms, bars

nigerian_mode_fit should be FALSE when:
- The business type is highly specific to another culture/country
- Nigerian cultural adaptation would feel forced or inaccurate
Examples: US sports bars, sushi bars, ski resorts, US-style diners
"""


# ── Load review texts per business ────────────────────────────────────────────

def _load_review_texts() -> dict[str, list[str]]:
    """Build business_id → top review snippets (sorted by quality_score desc)."""
    _log("Loading review texts for enrichment context…")
    by_biz: dict[str, list[tuple[float, str]]] = defaultdict(list)

    with open(PROCESSED / "yelp_reviews.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            bid = r.get("business_id", r.get("item_id", ""))
            text = r.get("text", "")[:REVIEW_SNIPPET_LEN]
            q = r.get("quality_score", 0.0)
            by_biz[bid].append((q, text))

    result: dict[str, list[str]] = {}
    for bid, pairs in by_biz.items():
        pairs.sort(reverse=True)
        result[bid] = [text for _, text in pairs[:REVIEWS_PER_ITEM]]

    _log(f"  Loaded review texts for {len(result)} businesses")
    return result


# ── Checkpoint ────────────────────────────────────────────────────────────────

def _needs_enrichment(item: dict) -> bool:
    """True if item is missing any enrichment field added by this script."""
    if not item.get("enriched"):
        return True
    attrs = item.get("attributes", {})
    if not attrs.get("top_topics"):
        return True
    if not attrs.get("sentiment_split"):
        return True
    return False


def _load_checkpoint() -> set[str]:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text()).get("enriched_ids", []))
    return set()


def _save_checkpoint(enriched_ids: set[str]) -> None:
    CHECKPOINT.write_text(json.dumps({"enriched_ids": sorted(enriched_ids)}, indent=2))


def _write_items(items_ordered: list[dict], enriched_results: dict[str, dict]) -> None:
    """Write-through: flush current enriched state to items.jsonl immediately.

    Uses a temp file + atomic rename so the file is never left in a partial state.
    """
    tmp = ITEMS_PATH.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for item in items_ordered:
            rec = enriched_results.get(item["item_id"], item)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(ITEMS_PATH)


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_batch_prompt(batch: list[dict], review_texts: dict[str, list[str]]) -> str:
    cat_list = "\n".join(f"  - {c}" for c in NIGERIAN_CATEGORIES)
    domain_list = " | ".join(DOMAINS)

    items_block = ""
    for i, item in enumerate(batch):
        snippets = review_texts.get(item["item_id"], [])
        snippet_block = "\n".join(
            f'  Review {j+1}: "{s}"' for j, s in enumerate(snippets)
        ) or "  (no review text available)"

        items_block += f"""
Item {i+1}:
  item_id: {item["item_id"]}
  Current inferred category: {item.get("nigerian_category", "unknown")}
  Current domain: {item.get("domain", "unknown")}
  Avg rating: {item.get("avg_rating", "?")} stars over {item.get("review_count", "?")} reviews
  Review snippets:
{snippet_block}
"""

    return f"""You are enriching a business database for a Nigerian review AI system.

For each business below, analyze the review snippets and return enriched metadata.

## Nigerian category options (pick the best fit, or use General* if none match well)
{cat_list}

## Domain options
{domain_list}

## Nigerian mode fit guidance
{NIGERIAN_FIT_GUIDE}

## Businesses to enrich
{items_block}

## Output
Return ONLY a valid JSON array with exactly {len(batch)} objects, one per business, in order.
No markdown. No explanation. No code fences.

Each object must have these exact keys:
  item_id         : (copy from input, do not change)
  name            : realistic business name inferred from reviews (if reviews mention a name, use it exactly; otherwise generate a plausible name matching the type)
  nigerian_category : best match from the category list above
  domain          : one of {domain_list}
  nigerian_mode_fit : true or false
  nigerian_fit_reason : one sentence explaining why
  description     : 1-2 clear sentences describing this business (60-120 words), suitable for semantic search embedding
  enrichment_confidence : float 0.0-1.0 (your confidence in the categorisation)
  top_topics      : JSON array of 3-5 short strings naming the key topics reviewers discuss (e.g. ["food quality", "service speed", "price value", "ambiance"]). Infer from review snippets. If no snippets, use category defaults.
  sentiment_split : JSON object with keys "positive", "neutral", "negative" — floats summing to 1.0, estimating the fraction of reviews with each sentiment based on the snippets and avg_rating.

[
  {{
    "item_id": "...",
    "name": "...",
    "nigerian_category": "...",
    "domain": "...",
    "nigerian_mode_fit": true,
    "nigerian_fit_reason": "...",
    "description": "...",
    "enrichment_confidence": 0.0,
    "top_topics": ["topic1", "topic2", "topic3"],
    "sentiment_split": {{"positive": 0.7, "neutral": 0.2, "negative": 0.1}}
  }},
  ...
]"""


# ── Response parser ───────────────────────────────────────────────────────────

def _parse_response(raw: str, batch: list[dict]) -> list[dict]:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []

    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    valid: list[dict] = []
    id_to_original = {item["item_id"]: item for item in batch}

    for obj in items:
        if not isinstance(obj, dict):
            continue
        item_id = obj.get("item_id", "")
        if item_id not in id_to_original:
            continue

        original = id_to_original[item_id]
        name = str(obj.get("name", "")).strip() or item_id
        nigerian_cat = str(obj.get("nigerian_category", "")).strip()
        if nigerian_cat not in NIGERIAN_CATEGORIES:
            nigerian_cat = original.get("nigerian_category", "General Restaurant")
        domain = str(obj.get("domain", "")).strip()
        if domain not in DOMAINS:
            domain = original.get("domain", "food")
        naija_fit = bool(obj.get("nigerian_mode_fit", True))
        description = str(obj.get("description", "")).strip()
        confidence = float(obj.get("enrichment_confidence", 0.5))

        # top_topics: must be a list of strings, 1-8 items
        raw_topics = obj.get("top_topics", [])
        top_topics: list[str] = (
            [str(t).strip() for t in raw_topics if str(t).strip()][:8]
            if isinstance(raw_topics, list)
            else []
        )

        # sentiment_split: must be {positive, neutral, negative} floats summing ~1.0
        raw_split = obj.get("sentiment_split", {})
        sentiment_split: dict[str, float] = {}
        if isinstance(raw_split, dict):
            pos = float(raw_split.get("positive", 0.0))
            neu = float(raw_split.get("neutral", 0.0))
            neg = float(raw_split.get("negative", 0.0))
            total = pos + neu + neg
            if total > 0:
                sentiment_split = {
                    "positive": round(pos / total, 3),
                    "neutral": round(neu / total, 3),
                    "negative": round(neg / total, 3),
                }

        valid.append({
            **original,
            "name": name,
            "nigerian_category": nigerian_cat,
            "domain": domain,
            "nigerian_mode_fit": naija_fit,
            "nigerian_fit_reason": str(obj.get("nigerian_fit_reason", "")).strip(),
            "description": description or original.get("description", ""),
            "enrichment_confidence": round(confidence, 3),
            "attributes": {
                "top_topics": top_topics,
                "sentiment_split": sentiment_split,
            },
            "enriched": True,
        })

    return valid


# ── Logger ────────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--reset-checkpoint", action="store_true")
    args = parser.parse_args()

    if args.reset_checkpoint and CHECKPOINT.exists():
        CHECKPOINT.unlink()
        _log("Checkpoint cleared")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: GEMINI_API_KEY not set in .env")
        sys.exit(1)
    if api_key.startswith("AIza-xxx") and not args.dry_run:
        print("ERROR: GEMINI_API_KEY is still the placeholder value")
        sys.exit(1)

    # Load raw items
    items: list[dict] = []
    with open(ITEMS_PATH, encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    _log(f"Loaded {len(items)} items from {ITEMS_PATH.name}")

    # Derive remaining from actual file contents, not just checkpoint.
    # This catches items enriched before top_topics/sentiment_split were added.
    remaining = [item for item in items if _needs_enrichment(item)]
    already_done_ids = {item["item_id"] for item in items if not _needs_enrichment(item)}
    _log(f"  {len(already_done_ids)} fully enriched, {len(remaining)} need enrichment")

    # Sync checkpoint to match file state
    if already_done_ids:
        _save_checkpoint(already_done_ids)

    batch_size = args.batch_size
    n_batches = (len(remaining) + batch_size - 1) // batch_size
    _log(f"  Batches: {n_batches} × {batch_size} items ≈ {n_batches * CALL_DELAY_S / 60:.1f} min")

    if args.dry_run:
        _log("DRY RUN — no LLM calls")
        # Show what first batch would look like
        review_texts = _load_review_texts()
        sample_batch = remaining[:batch_size]
        print("\n--- Sample batch prompt (first 800 chars) ---")
        prompt = _build_batch_prompt(sample_batch, review_texts)
        print(prompt[:800])
        return

    # Load review texts for context
    review_texts = _load_review_texts()

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    llm = ChatGoogleGenerativeAI(
        model=MODEL,
        google_api_key=api_key,
        temperature=0.3,        # low temp — this is classification, not generation
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    enriched_results: dict[str, dict] = {item["item_id"]: item for item in items}
    enriched_ids = set(already_done_ids)
    failed_ids: list[str] = []

    for batch_idx in range(n_batches):
        start = batch_idx * batch_size
        batch = remaining[start: start + batch_size]
        if not batch:
            break

        batch_ids = [item["item_id"] for item in batch]
        _log(f"[{batch_idx+1}/{n_batches}] Enriching {len(batch)} items…")

        for attempt in range(MAX_RETRIES):
            try:
                prompt = _build_batch_prompt(batch, review_texts)
                response = llm.invoke([HumanMessage(content=prompt)])
                parsed = _parse_response(str(response.content), batch)

                if len(parsed) < len(batch) * 0.6:
                    _log(f"  WARN: only {len(parsed)}/{len(batch)} parsed — retry {attempt+1}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2)
                        continue

                for rec in parsed:
                    enriched_results[rec["item_id"]] = rec
                    enriched_ids.add(rec["item_id"])

                failed_batch = [bid for bid in batch_ids if bid not in {r["item_id"] for r in parsed}]
                if failed_batch:
                    failed_ids.extend(failed_batch)
                    _log(f"  WARN: {len(failed_batch)} items not parsed in this batch")

                _save_checkpoint(enriched_ids)

                # Write-through: flush to items.jsonl immediately after each batch
                _write_items(items, enriched_results)

                # Sample log
                if parsed:
                    s = parsed[0]
                    topics_preview = s.get("attributes", {}).get("top_topics", [])[:3]
                    done_so_far = len(enriched_ids)
                    _log(
                        f"  OK: '{s['name']}' | {s['nigerian_category']} | "
                        f"naija_fit={s['nigerian_mode_fit']} | conf={s['enrichment_confidence']} | "
                        f"topics={topics_preview} | "
                        f"saved={done_so_far}/{len(items)}"
                    )
                break

            except Exception as exc:
                err = str(exc)
                if "API_KEY_INVALID" in err or "API key not valid" in err:
                    print("\nERROR: Invalid API key. Check GEMINI_API_KEY in .env")
                    sys.exit(1)
                is_retryable = any(x in err.lower() for x in ("429", "quota", "rate", "500", "503"))
                if is_retryable and attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    _log(f"  Rate limit — waiting {wait}s")
                    time.sleep(wait)
                else:
                    _log(f"  ERROR [{type(exc).__name__}]: {err[:150]}")
                    failed_ids.extend(batch_ids)
                    break

        time.sleep(CALL_DELAY_S)

    # Final flush (catches anything not flushed in last batch due to error path)
    _write_items(items, enriched_results)

    enriched_count = sum(1 for r in enriched_results.values() if r.get("enriched"))
    still_missing = sum(1 for r in enriched_results.values() if _needs_enrichment(r))
    naija_fit_count = sum(1 for r in enriched_results.values() if r.get("nigerian_mode_fit"))

    _log(f"\nEnrichment complete:")
    _log(f"  {enriched_count}/{len(items)} items fully enriched")
    _log(f"  {still_missing} items still incomplete (re-run to retry failed batches)")
    _log(f"  {naija_fit_count} items flagged nigerian_mode_fit=True")
    _log(f"  {len(failed_ids)} batch failures")
    _log(f"  Wrote → {ITEMS_PATH.relative_to(ROOT)}")
    if failed_ids:
        _log("  Re-run to retry failed items (checkpoint will skip successful ones)")

    enriched_count = sum(1 for r in final_items if r.get("enriched"))
    naija_fit_count = sum(1 for r in final_items if r.get("nigerian_mode_fit"))

    _log(f"\nEnrichment complete:")
    _log(f"  {enriched_count}/{len(final_items)} items enriched")
    _log(f"  {naija_fit_count} items flagged nigerian_mode_fit=True")
    _log(f"  {len(failed_ids)} items failed (kept original values)")
    _log(f"  Wrote → {ITEMS_PATH.relative_to(ROOT)}")

    if failed_ids:
        _log(f"  Re-run to retry failed items (checkpoint will skip successful ones)")


if __name__ == "__main__":
    main()
