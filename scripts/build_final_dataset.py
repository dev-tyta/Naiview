"""Build the final unified dataset for Task A + Task B training and evaluation.

Combines:
  1. Yelp reviews (46K, processed) → converted to unified schema
  2. Synthetic Nigerian reviews (540) → already in unified schema

Outputs:
  data/processed/final_dataset.jsonl      — all reviews, unified schema
  data/processed/user_histories.jsonl     — per-user review history (Task A input)
  data/processed/items.jsonl              — per-business item corpus (Task B FAISS/BM25 index)
  data/processed/eval/task_a_train.jsonl  — Task A training reviews
  data/processed/eval/task_a_test.jsonl   — Task A held-out ground truth (leave-one-out)
  data/processed/eval/task_b_train.jsonl  — Task B training interactions
  data/processed/eval/task_b_test.jsonl   — Task B held-out items (leave-one-out)

Eval protocol:
  Task A — leave-one-out per user: hold out last review (by date) as generation target.
           Eval: ROUGE-L + BERTScore(generated vs held-out) + |predicted_stars - actual|.
           naija_mode=false uses standard English metrics.
           naija_mode=true  uses Abeg score thresholds on top.

  Task B — leave-one-out per user: hold out last visited business as recommendation target.
           Eval: Hit@10, NDCG@10.
           Both modes share same item corpus; mode only affects explanation register.

Minimum requirements:
  - User needs ≥ 3 reviews to appear in eval (else cold-start path, excluded here).
  - Business needs ≥ 3 reviews total to appear in item corpus.

Run:
  python3 scripts/build_final_dataset.py
  python3 scripts/build_final_dataset.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data" / "processed"
SYNTHETIC = ROOT / "data" / "synthetic"
RAW = ROOT / "data" / "raw"
EVAL_DIR = PROCESSED / "eval"

# ── Config ────────────────────────────────────────────────────────────────────

MIN_USER_REVIEWS = 3        # users below this go to cold-start, excluded from eval
MIN_ITEM_REVIEWS = 3        # businesses below this excluded from item corpus
TRAIN_RATIO = 0.9           # 90% train / 10% test split on users


# ── Category inference from taxonomy keywords ─────────────────────────────────

def _build_keyword_map() -> dict[str, tuple[str, str, str]]:
    """Return {keyword: (nigerian_category, yelp_category, domain)} lookup."""
    taxonomy_path = RAW / "nigerian_taxonomy.json"
    mapping: dict[str, tuple[str, str, str]] = {}
    domain_map = {
        "Buka / Mama Put": "food", "Suya Joint / Street Food": "food",
        "Eateries (Mr Biggs-style)": "food", "Pepper Soup Spot": "food",
        "Beer Parlour": "food", "Canteen / Bukateria": "food",
        "Confectionery / Bakery": "food", "Open Market Stall": "retail",
        "Guesthouse / Lodge": "hospitality", "Beauty / Salon": "services",
    }
    yelp_equiv = {
        "Buka / Mama Put": "Restaurants", "Suya Joint / Street Food": "Barbeque",
        "Eateries (Mr Biggs-style)": "Fast Food", "Pepper Soup Spot": "African",
        "Beer Parlour": "Bars", "Canteen / Bukateria": "Cafes",
        "Confectionery / Bakery": "Bakeries", "Open Market Stall": "Shopping",
        "Guesthouse / Lodge": "Hotels & Travel", "Beauty / Salon": "Beauty & Spas",
    }
    if taxonomy_path.exists():
        raw = json.loads(taxonomy_path.read_text())
        for m in raw.get("mappings", []):
            cat = m["nigerian_category"]
            for kw in m.get("typical_keywords", []):
                mapping[kw.lower()] = (
                    cat,
                    yelp_equiv.get(cat, "Restaurants"),
                    domain_map.get(cat, "food"),
                )
    return mapping


def _infer_category(text: str, kw_map: dict) -> tuple[str, str, str, float]:
    """Return (nigerian_category, yelp_category, domain, confidence)."""
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    scores: dict[str, int] = defaultdict(int)
    for tok in tokens:
        if tok in kw_map:
            cat = kw_map[tok][0]
            scores[cat] += 1
    if not scores:
        return "Restaurants", "Restaurants", "food", 0.0
    best_cat = max(scores, key=lambda c: scores[c])
    total = sum(scores.values())
    conf = round(scores[best_cat] / total, 3)
    cat_info = kw_map[next(k for k in kw_map if kw_map[k][0] == best_cat)]
    return best_cat, cat_info[1], cat_info[2], conf


# ── Unified schema helpers ────────────────────────────────────────────────────

def _yelp_to_unified(r: dict, kw_map: dict) -> dict:
    """Convert a processed Yelp review record to the unified dataset schema."""
    text = r.get("text", "")
    stars = int(r.get("stars", 3))
    sentiment = r.get("sentiment", "neutral")
    nigerian_cat, yelp_cat, domain, cat_conf = _infer_category(text, kw_map)

    return {
        "review_id": r.get("review_id", ""),
        "user_id": r.get("user_id", ""),
        "item_id": r.get("business_id", ""),
        "text": text,
        "stars": stars,
        "sentiment": sentiment,
        "tier": r.get("tier", "neutral"),
        "register": "natural",
        "naija_mode": False,
        "category": nigerian_cat,
        "yelp_category": yelp_cat,
        "domain": domain,
        "category_confidence": cat_conf,
        "region": "Unknown",
        "pidgin_density": 0.0,
        "text_len": r.get("text_len", len(text)),
        "quality_score": r.get("quality_score", 0.0),
        "nigerian_context_score": r.get("nigerian_context_score", 0.0),
        "engagement": r.get("engagement", 0),
        "date": r.get("date", ""),
        "source": "yelp",
        "eval_text_quality": True,
        "eval_rating_accuracy": True,
        "eval_cross_domain": True,
    }


def _synthetic_to_unified(r: dict) -> dict:
    """Normalise a synthetic review record to the unified schema."""
    return {
        "review_id": r.get("review_id", ""),
        "user_id": f"synthetic_{r.get('region','gen')}_{r.get('category','cat')[:8]}",
        "item_id": f"syn_item_{r.get('category','cat')[:12].replace(' ','_').replace('/','_')}",
        "text": r.get("text", ""),
        "stars": r.get("stars", 3),
        "sentiment": r.get("sentiment", "neutral"),
        "tier": {"positive": "positive", "negative": "negative", "neutral": "neutral"}.get(
            r.get("sentiment", "neutral"), "neutral"
        ),
        "register": r.get("register", "natural"),
        "naija_mode": r.get("naija_mode", False),
        "category": r.get("category", ""),
        "yelp_category": r.get("yelp_category", "Restaurants"),
        "domain": r.get("domain", "food"),
        "category_confidence": 1.0,
        "region": r.get("region", "general"),
        "pidgin_density": r.get("pidgin_density", 0.0),
        "text_len": r.get("text_len", 0),
        "quality_score": 0.8,
        "nigerian_context_score": r.get("pidgin_density", 0.0),
        "engagement": 0,
        "date": "",
        "source": "synthetic",
        "eval_text_quality": r.get("eval_text_quality", True),
        "eval_rating_accuracy": r.get("eval_rating_accuracy", True),
        "eval_cross_domain": r.get("eval_cross_domain", False),
    }


# ── Item corpus builder ───────────────────────────────────────────────────────

def _build_items(yelp_records: list[dict]) -> list[dict]:
    """Aggregate Yelp reviews by business_id → Item objects.

    Description = concatenation of top-3 reviews by quality_score.
    Category = majority vote of category_confidence-weighted inferences.
    """
    biz: dict[str, dict] = defaultdict(lambda: {
        "stars_sum": 0, "count": 0, "texts": [], "categories": defaultdict(float),
        "yelp_categories": defaultdict(float), "domains": defaultdict(float),
        "best_quality": 0.0,
    })

    for r in yelp_records:
        bid = r["item_id"]
        biz[bid]["stars_sum"] += r["stars"]
        biz[bid]["count"] += 1
        conf = r.get("category_confidence", 0.0)
        biz[bid]["categories"][r["category"]] += conf + 0.1
        biz[bid]["yelp_categories"][r["yelp_category"]] += 1
        biz[bid]["domains"][r["domain"]] += 1
        q = r.get("quality_score", 0.0)
        if q >= biz[bid]["best_quality"] and len(biz[bid]["texts"]) < 3:
            biz[bid]["texts"].append(r["text"][:300])
            biz[bid]["best_quality"] = q

    items = []
    for bid, data in biz.items():
        if data["count"] < MIN_ITEM_REVIEWS:
            continue

        avg_rating = round(data["stars_sum"] / data["count"], 2)
        category = max(data["categories"], key=lambda c: data["categories"][c])
        yelp_cat = max(data["yelp_categories"], key=lambda c: data["yelp_categories"][c])
        domain = max(data["domains"], key=lambda d: data["domains"][d])

        # Build description from top review snippets
        description = " ".join(data["texts"][:2]).strip()
        if not description:
            description = f"{category} with {data['count']} reviews."

        items.append({
            "item_id": bid,
            "name": bid,                # no business names in Yelp review CSV
            "category": yelp_cat,
            "nigerian_category": category,
            "domain": domain,
            "avg_rating": avg_rating,
            "review_count": data["count"],
            "description": description,
            "attributes": {
                "top_topics": [],      # populated later by retrieval tool
                "sentiment_split": {},
            },
        })

    return items


# ── Eval split builder ────────────────────────────────────────────────────────

def _build_eval_splits(
    yelp_records: list[dict],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Leave-one-out splits for Task A + Task B.

    Task A: hold out each user's last review (by date) → generation ground truth
    Task B: hold out each user's last business → recommendation ground truth

    Returns: (task_a_train, task_a_test, task_b_train, task_b_test)
    """
    # Group by user, sort by date
    by_user: dict[str, list[dict]] = defaultdict(list)
    for r in yelp_records:
        by_user[r["user_id"]].append(r)

    # Sort each user's reviews chronologically
    for uid in by_user:
        by_user[uid].sort(key=lambda r: r.get("date", ""), reverse=False)

    # Only include users with enough history
    eligible_users = [uid for uid, reviews in by_user.items() if len(reviews) >= MIN_USER_REVIEWS]

    # 90/10 user-level split so test users are unseen during training
    split_idx = int(len(eligible_users) * TRAIN_RATIO)
    train_users = set(eligible_users[:split_idx])
    test_users = set(eligible_users[split_idx:])

    task_a_train: list[dict] = []
    task_a_test: list[dict] = []
    task_b_train: list[dict] = []
    task_b_test: list[dict] = []

    for uid in train_users:
        reviews = by_user[uid]
        # All reviews go to train for Task A
        task_a_train.extend(reviews)
        # All but last business go to Task B train; last is B test
        task_b_train.extend({
            "user_id": r["user_id"],
            "item_id": r["item_id"],
            "stars": r["stars"],
            "date": r["date"],
        } for r in reviews[:-1])
        last = reviews[-1]
        task_b_train.append({
            "user_id": last["user_id"],
            "item_id": last["item_id"],
            "stars": last["stars"],
            "date": last["date"],
        })

    for uid in test_users:
        reviews = by_user[uid]
        # All but last review → train (context for generation)
        task_a_train.extend(reviews[:-1])
        # Last review → test (ground truth for generation)
        task_a_test.append({
            **reviews[-1],
            "history_reviews": [r["review_id"] for r in reviews[:-1]],
        })
        # All but last item → B train; last item → B test
        for r in reviews[:-1]:
            task_b_train.append({
                "user_id": r["user_id"], "item_id": r["item_id"],
                "stars": r["stars"], "date": r["date"],
            })
        last = reviews[-1]
        task_b_test.append({
            "user_id": last["user_id"],
            "item_id": last["item_id"],
            "stars": last["stars"],
            "date": last["date"],
            "history_item_ids": [r["item_id"] for r in reviews[:-1]],
        })

    return task_a_train, task_a_test, task_b_train, task_b_test


# ── User history builder ──────────────────────────────────────────────────────

def _build_user_histories(yelp_records: list[dict]) -> list[dict]:
    """Aggregate reviews per user → UserHistory objects for fingerprinting."""
    by_user: dict[str, list[dict]] = defaultdict(list)
    for r in yelp_records:
        by_user[r["user_id"]].append(r)

    histories = []
    for uid, reviews in by_user.items():
        if len(reviews) < MIN_USER_REVIEWS:
            continue
        reviews_sorted = sorted(reviews, key=lambda r: r.get("date", ""))
        histories.append({
            "user_id": uid,
            "review_count": len(reviews_sorted),
            "earliest_review": reviews_sorted[0].get("date", ""),
            "latest_review": reviews_sorted[-1].get("date", ""),
            "avg_stars": round(sum(r["stars"] for r in reviews_sorted) / len(reviews_sorted), 2),
            "review_ids": [r["review_id"] for r in reviews_sorted],
            "item_ids": [r["item_id"] for r in reviews_sorted],
        })

    return histories


# ── Logger ────────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Stats only, no writes")
    args = parser.parse_args()

    if args.dry_run:
        _log("DRY RUN — no files written")

    # ── 1. Load Yelp reviews ────────────────────────────────────────
    _log("Loading Yelp reviews…")
    kw_map = _build_keyword_map()

    yelp_unified: list[dict] = []
    with open(PROCESSED / "yelp_reviews.jsonl") as f:
        for line in f:
            yelp_unified.append(_yelp_to_unified(json.loads(line), kw_map))
    _log(f"  Yelp: {len(yelp_unified)} reviews loaded")

    # ── 2. Load synthetic reviews ───────────────────────────────────
    _log("Loading synthetic reviews…")
    synthetic_unified: list[dict] = []
    syn_path = SYNTHETIC / "nigerian_reviews.jsonl"
    if syn_path.exists():
        with open(syn_path) as f:
            for line in f:
                synthetic_unified.append(_synthetic_to_unified(json.loads(line)))
    _log(f"  Synthetic: {len(synthetic_unified)} reviews loaded")

    # ── 3. Combined final dataset ───────────────────────────────────
    final_dataset = yelp_unified + synthetic_unified
    _log(f"  Combined: {len(final_dataset)} total reviews")

    # Domain distribution
    domain_counts: dict[str, int] = defaultdict(int)
    for r in final_dataset:
        domain_counts[r["domain"]] += 1
    _log(f"  Domain dist: {dict(domain_counts)}")

    naija_counts = sum(1 for r in final_dataset if r["naija_mode"])
    _log(f"  naija_mode=True: {naija_counts} | naija_mode=False: {len(final_dataset)-naija_counts}")

    # ── 4. User histories ───────────────────────────────────────────
    _log("Building user histories…")
    histories = _build_user_histories(yelp_unified)
    _log(f"  {len(histories)} users with ≥{MIN_USER_REVIEWS} reviews")

    # ── 5. Item corpus ──────────────────────────────────────────────
    _log("Building item corpus…")
    items = _build_items(yelp_unified)
    domain_items: dict[str, int] = defaultdict(int)
    for item in items:
        domain_items[item["domain"]] += 1
    _log(f"  {len(items)} items (≥{MIN_ITEM_REVIEWS} reviews) | domain dist: {dict(domain_items)}")

    # ── 6. Eval splits ──────────────────────────────────────────────
    _log("Building eval splits (leave-one-out)…")
    ta_train, ta_test, tb_train, tb_test = _build_eval_splits(yelp_unified)
    _log(f"  Task A — train: {len(ta_train)} | test: {len(ta_test)}")
    _log(f"  Task B — train: {len(tb_train)} | test: {len(tb_test)}")

    # Avg reviews per test user
    if ta_test:
        avg_hist = sum(len(r.get("history_reviews", [])) for r in ta_test) / len(ta_test)
        _log(f"  Task A test — avg history length: {avg_hist:.1f} reviews")

    if args.dry_run:
        _log("Dry run complete — no files written")
        return

    # ── 7. Write outputs ────────────────────────────────────────────
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    def _write_jsonl(path: Path, records: list[dict]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log(f"  Wrote {len(records):,} records → {path.relative_to(ROOT)}")

    _write_jsonl(PROCESSED / "final_dataset.jsonl", final_dataset)
    _write_jsonl(PROCESSED / "user_histories.jsonl", histories)
    _write_jsonl(PROCESSED / "items.jsonl", items)
    _write_jsonl(EVAL_DIR / "task_a_train.jsonl", ta_train)
    _write_jsonl(EVAL_DIR / "task_a_test.jsonl", ta_test)
    _write_jsonl(EVAL_DIR / "task_b_train.jsonl", tb_train)
    _write_jsonl(EVAL_DIR / "task_b_test.jsonl", tb_test)

    _log("Done")


if __name__ == "__main__":
    main()
