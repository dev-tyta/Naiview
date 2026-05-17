"""Data processing pipeline — raw → processed.

Inputs (data/raw/):
  yelp_sampled_100k.csv       — Yelp review corpus
  afrisenti_pidgin_full.csv   — Nigerian Pidgin tweets (sentiment)
  nigerian_taxonomy.json      — Category mappings + context features + regional markers

Outputs (data/processed/):
  yelp_reviews.jsonl          — Cleaned Yelp reviews: quality-filtered, user-capped,
                                Nigerian context relevance scored
  pidgin_examples.jsonl       — AfriSenti tweets: normalized + pidgin density scored
  few_shots.jsonl             — Balanced few-shot examples for prompt templates
                                (~250 per sentiment tier, highest quality first)
  taxonomy.json               — Merged taxonomy: category map + features + regions

Outputs (data/phrase_library/):
  examples_by_sentiment.json  — Top pidgin examples grouped pos/neu/neg
  category_examples.json      — Example review tones per Nigerian category
  context_features.json       — Context feature keywords per dimension
  regional_markers.json       — Region → location markers lookup

Run:
  python3 scripts/process_data.py
  python3 scripts/process_data.py --dry-run   # stats only, no writes
  python3 scripts/process_data.py --step yelp  # single step
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PHRASE_LIB = ROOT / "data" / "phrase_library"


# ── Config ────────────────────────────────────────────────────────────────────

# Yelp
YELP_MIN_TEXT_LEN = 50
YELP_MAX_TEXT_LEN = 1500
YELP_MAX_REVIEWS_PER_USER = 5      # cap bias from prolific reviewers
YELP_QUALITY_MIN_ENGAGEMENT = 1    # useful+funny+cool >= this OR stars in {1, 5}

# AfriSenti
AFRISENTI_MIN_TEXT_LEN = 15

# Few-shot subset
FEW_SHOT_PER_TIER = 250            # per sentiment tier (very_negative…very_positive)


# ── Pidgin/Nigerian word sets ─────────────────────────────────────────────────

# Core Pidgin & Nigerian English markers for density scoring.
# Loaded from taxonomy at runtime; these are fallback seeds.
_PIDGIN_SEEDS = {
    "dey", "na", "dem", "abeg", "oga", "wahala", "sha", "sef", "nna", "wey",
    "chop", "belle", "gbege", "abi", "shey", "no be", "e don", "wetin",
    "jollof", "suya", "egusi", "amala", "fufu", "pounded", "buka", "mama put",
    "nepa", "phcn", "light", "generator", "ghen ghen", "no cap", "naija",
    "lagosian", "ehen", "ehn", "oya", "mumu", "ode", "agidi", "eba",
}

# Nigerian English context keywords (from taxonomy context_features)
_CONTEXT_KEYWORDS: set[str] = set()


def _load_context_keywords() -> None:
    taxonomy_path = RAW / "nigerian_taxonomy.json"
    if not taxonomy_path.exists():
        return
    raw = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    for keywords in raw.get("nigerian_context_features", {}).values():
        _CONTEXT_KEYWORDS.update(k.lower() for k in keywords)
    # Also add typical_keywords from category mappings
    for mapping in raw.get("mappings", []):
        for kw in mapping.get("typical_keywords", []):
            _CONTEXT_KEYWORDS.update(kw.lower().split())


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_whitespace(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


def _truncate_at_sentence(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    chunk = text[:max_len]
    for sep in (".", "!", "?"):
        idx = chunk.rfind(sep)
        if idx > max_len * 0.6:
            return chunk[: idx + 1].strip()
    idx = chunk.rfind(" ")
    return (chunk[:idx] if idx > 0 else chunk).strip() + "…"


def _stars_to_sentiment(stars: int) -> str:
    if stars <= 2:
        return "negative"
    if stars == 3:
        return "neutral"
    return "positive"


def _stars_to_tier(stars: int) -> str:
    if stars == 1:
        return "very_negative"
    if stars == 2:
        return "negative"
    if stars == 3:
        return "neutral"
    if stars == 4:
        return "positive"
    return "very_positive"


def _pidgin_density(text: str) -> float:
    """Ratio of tokens that are Pidgin/Nigerian markers. Range 0.0–1.0."""
    tokens = re.findall(r"[a-z']+", text.lower())
    if not tokens:
        return 0.0
    all_markers = _PIDGIN_SEEDS | _CONTEXT_KEYWORDS
    hits = sum(1 for t in tokens if t in all_markers)
    return round(hits / len(tokens), 4)


def _nigerian_context_score(text: str) -> float:
    """Score 0.0–1.0: how much this Yelp review touches Nigerian concerns.

    Uses log-scaled hit count against the context_features keyword set.
    High score → more useful as a transfer example for Nigerian context.
    """
    if not _CONTEXT_KEYWORDS:
        return 0.0
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    hits = len(tokens & _CONTEXT_KEYWORDS)
    if hits == 0:
        return 0.0
    # log scale: 1 hit→~0.25, 3 hits→~0.5, 8 hits→~0.75, 20 hits→~1.0
    return round(min(1.0, math.log1p(hits) / math.log1p(20)), 4)


def _quality_score(stars: int, engagement: int, text_len: int) -> float:
    """Composite quality score 0.0–1.0 for ranking few-shot candidates.

    Factors: engagement (log-scaled), text length (sweet spot 150-800),
    and star extremity (1 or 5 are more opinion-dense).
    """
    eng_score = min(1.0, math.log1p(engagement) / math.log1p(50))
    # sweet spot: 150–800 chars
    if text_len < 150:
        len_score = text_len / 150
    elif text_len <= 800:
        len_score = 1.0
    else:
        len_score = max(0.5, 1.0 - (text_len - 800) / 1400)
    star_extremity = 1.0 if stars in (1, 5) else 0.7 if stars in (2, 4) else 0.4
    return round(0.45 * eng_score + 0.35 * len_score + 0.20 * star_extremity, 4)


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Yelp processing ───────────────────────────────────────────────────────────

def process_yelp(dry_run: bool) -> list[dict]:
    path = RAW / "yelp_sampled_100k.csv"
    _log(f"Yelp → reading {path.name}")

    user_counts: dict[str, int] = defaultdict(int)
    kept: list[dict] = []
    stats = {
        "total": 0,
        "dropped_empty": 0,
        "dropped_short": 0,
        "dropped_quality": 0,
        "dropped_user_cap": 0,
        "truncated": 0,
        "kept": 0,
        "by_stars": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        "by_sentiment": {"negative": 0, "neutral": 0, "positive": 0},
    }

    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total"] += 1

            text = (row.get("text") or "").strip()
            if not text:
                stats["dropped_empty"] += 1
                continue

            text = _normalize_whitespace(text)
            if len(text) < YELP_MIN_TEXT_LEN:
                stats["dropped_short"] += 1
                continue

            stars = int(row.get("stars", 3))
            useful = int(row.get("useful") or 0)
            funny = int(row.get("funny") or 0)
            cool = int(row.get("cool") or 0)
            engagement = useful + funny + cool

            # Quality gate: must have engagement OR be an extreme rating
            if engagement < YELP_QUALITY_MIN_ENGAGEMENT and stars not in (1, 5):
                stats["dropped_quality"] += 1
                continue

            user_id = row.get("user_id", "")
            if user_counts[user_id] >= YELP_MAX_REVIEWS_PER_USER:
                stats["dropped_user_cap"] += 1
                continue
            user_counts[user_id] += 1

            if len(text) > YELP_MAX_TEXT_LEN:
                text = _truncate_at_sentence(text, YELP_MAX_TEXT_LEN)
                stats["truncated"] += 1

            sentiment = _stars_to_sentiment(stars)
            ctx_score = _nigerian_context_score(text)
            q_score = _quality_score(stars, engagement, len(text))

            record = {
                "review_id": row.get("review_id", ""),
                "user_id": user_id,
                "business_id": row.get("business_id", ""),
                "stars": stars,
                "sentiment": sentiment,
                "tier": _stars_to_tier(stars),
                "engagement": engagement,
                "quality_score": q_score,
                "nigerian_context_score": ctx_score,
                "text": text,
                "text_len": len(text),
                "date": row.get("date", ""),
            }
            kept.append(record)
            stats["by_stars"][stars] += 1
            stats["by_sentiment"][sentiment] += 1
            stats["kept"] += 1

    _log(
        f"Yelp — total:{stats['total']} kept:{stats['kept']} "
        f"dropped_quality:{stats['dropped_quality']} "
        f"dropped_user_cap:{stats['dropped_user_cap']} "
        f"dropped_short:{stats['dropped_short']} truncated:{stats['truncated']}"
    )
    _log(f"Yelp — sentiment: {stats['by_sentiment']}  stars: {stats['by_stars']}")
    _log(f"Yelp — unique users after cap: {len(user_counts)}")

    if not dry_run:
        out = PROCESSED / "yelp_reviews.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for rec in kept:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log(f"Yelp → wrote {len(kept):,} records → {out.relative_to(ROOT)}")

    return kept


# ── AfriSenti processing ──────────────────────────────────────────────────────

def process_afrisenti(dry_run: bool) -> list[dict]:
    path = RAW / "afrisenti_pidgin_full.csv"
    _log(f"AfriSenti → reading {path.name}")

    kept: list[dict] = []
    by_label: dict[str, int] = {}
    dropped_short = 0

    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = _normalize_whitespace(row.get("tweet") or "")
            label = (row.get("label") or "").strip().lower()

            if len(text) < AFRISENTI_MIN_TEXT_LEN:
                dropped_short += 1
                continue

            density = _pidgin_density(text)
            record = {
                "text": text,
                "label": label,
                "text_len": len(text),
                "pidgin_density": density,
            }
            kept.append(record)
            by_label[label] = by_label.get(label, 0) + 1

    _log(f"AfriSenti — kept:{len(kept)} dropped_short:{dropped_short} label dist:{by_label}")

    avg_density = sum(r["pidgin_density"] for r in kept) / len(kept) if kept else 0
    _log(f"AfriSenti — avg pidgin_density:{avg_density:.3f}")

    if not dry_run:
        out = PROCESSED / "pidgin_examples.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for rec in kept:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log(f"AfriSenti → wrote {len(kept):,} records → {out.relative_to(ROOT)}")

    return kept


# ── Few-shot subset ───────────────────────────────────────────────────────────

def build_few_shots(yelp_records: list[dict], dry_run: bool) -> None:
    """Build a balanced, high-quality few-shot subset from processed Yelp records.

    Selects top-N by quality_score per tier. Used by prompt templates for
    few-shot review generation (Task A).
    """
    _log(f"Few-shots → selecting top {FEW_SHOT_PER_TIER} per tier")

    by_tier: dict[str, list[dict]] = defaultdict(list)
    for rec in yelp_records:
        by_tier[rec["tier"]].append(rec)

    selected: list[dict] = []
    tier_counts: dict[str, int] = {}

    for tier, records in by_tier.items():
        # Sort by quality_score desc, then nigerian_context_score desc as tiebreak
        records.sort(key=lambda r: (r["quality_score"], r["nigerian_context_score"]), reverse=True)
        top = records[:FEW_SHOT_PER_TIER]
        # Slim the record for few-shot use (only text + metadata prompts need)
        for r in top:
            selected.append({
                "tier": r["tier"],
                "stars": r["stars"],
                "sentiment": r["sentiment"],
                "quality_score": r["quality_score"],
                "nigerian_context_score": r["nigerian_context_score"],
                "engagement": r["engagement"],
                "text": r["text"],
            })
        tier_counts[tier] = len(top)

    _log(f"Few-shots — {sum(tier_counts.values())} total: {tier_counts}")

    if not dry_run:
        out = PROCESSED / "few_shots.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for rec in selected:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log(f"Few-shots → wrote {len(selected):,} records → {out.relative_to(ROOT)}")


# ── Taxonomy processing ───────────────────────────────────────────────────────

def process_taxonomy(dry_run: bool) -> None:
    _log("Taxonomy → merging sources")

    raw_taxonomy = json.loads((RAW / "nigerian_taxonomy.json").read_text(encoding="utf-8"))

    category_map: dict[str, dict] = {}
    for mapping in raw_taxonomy.get("mappings", []):
        nigerian_name = mapping["nigerian_category"]
        entry = {
            "nigerian_name": nigerian_name,
            "description": mapping.get("description", ""),
            "keywords": mapping.get("typical_keywords", []),
            "example_tone": mapping.get("example_review_tone", ""),
        }
        for yelp_cat in mapping.get("yelp_equivalents", []):
            category_map[yelp_cat] = entry

    yaml_path = ROOT / "data" / "taxonomy.yaml"
    if yaml_path.exists():
        for line in yaml_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                parts = line.split(":", 1)
                yelp_cat = parts[0].strip().strip('"')
                nigerian_name = parts[1].strip().strip('"')
                if yelp_cat not in category_map:
                    category_map[yelp_cat] = {
                        "nigerian_name": nigerian_name,
                        "description": "",
                        "keywords": [],
                        "example_tone": "",
                    }
                else:
                    category_map[yelp_cat]["nigerian_name"] = nigerian_name

    merged = {
        "category_map": category_map,
        "context_features": raw_taxonomy.get("nigerian_context_features", {}),
        "regional_markers": raw_taxonomy.get("regional_markers", {}),
        "meta": {
            "sources": ["nigerian_taxonomy.json", "taxonomy.yaml"],
            "category_count": len(category_map),
            "regions": list(raw_taxonomy.get("regional_markers", {}).keys()),
        },
    }

    _log(
        f"Taxonomy — {len(category_map)} categories, "
        f"{len(merged['context_features'])} feature dims, "
        f"{len(merged['regional_markers'])} regions"
    )

    if not dry_run:
        out = PROCESSED / "taxonomy.json"
        out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"Taxonomy → wrote {out.relative_to(ROOT)}")


# ── Phrase library ────────────────────────────────────────────────────────────

def build_phrase_library(afrisenti_records: list[dict], dry_run: bool) -> None:
    _log("Phrase library → building")

    raw_taxonomy = json.loads((RAW / "nigerian_taxonomy.json").read_text(encoding="utf-8"))

    # Category examples from taxonomy
    category_examples: dict[str, dict] = {}
    for mapping in raw_taxonomy.get("mappings", []):
        cat = mapping["nigerian_category"]
        category_examples[cat] = {
            "description": mapping.get("description", ""),
            "yelp_equivalents": mapping.get("yelp_equivalents", []),
            "keywords": mapping.get("typical_keywords", []),
            "example_tone": mapping.get("example_review_tone", ""),
        }

    # Pidgin examples: top-200 per label, ranked by pidgin_density desc
    by_sentiment: dict[str, list[str]] = {"positive": [], "neutral": [], "negative": []}
    cap = 200
    label_records: dict[str, list[dict]] = defaultdict(list)
    for rec in afrisenti_records:
        label_records[rec["label"]].append(rec)

    for label in by_sentiment:
        candidates = label_records.get(label, [])
        candidates.sort(key=lambda r: r["pidgin_density"], reverse=True)
        by_sentiment[label] = [r["text"] for r in candidates[:cap]]

    _log(
        f"Phrase library — {len(category_examples)} categories, "
        f"pidgin examples: { {k: len(v) for k, v in by_sentiment.items()} }"
    )

    if not dry_run:
        files = {
            "category_examples.json": category_examples,
            "examples_by_sentiment.json": by_sentiment,
            "context_features.json": raw_taxonomy.get("nigerian_context_features", {}),
            "regional_markers.json": raw_taxonomy.get("regional_markers", {}),
        }
        for fname, data in files.items():
            out = PHRASE_LIB / fname
            out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            _log(f"Phrase library → wrote {out.relative_to(ROOT)}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="NaijaReview data processing pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Stats only, no file writes")
    parser.add_argument(
        "--step",
        choices=["yelp", "afrisenti", "taxonomy", "phrases", "all"],
        default="all",
    )
    args = parser.parse_args()

    if args.dry_run:
        _log("DRY RUN — no files will be written")

    if not args.dry_run:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        PHRASE_LIB.mkdir(parents=True, exist_ok=True)

    _load_context_keywords()
    _log(f"Loaded {len(_CONTEXT_KEYWORDS)} Nigerian context keywords + {len(_PIDGIN_SEEDS)} Pidgin seeds")

    t0 = datetime.now()
    step = args.step

    yelp_records: list[dict] = []
    afrisenti_records: list[dict] = []

    if step in ("yelp", "all"):
        yelp_records = process_yelp(args.dry_run)

    if step in ("afrisenti", "all"):
        afrisenti_records = process_afrisenti(args.dry_run)

    if step in ("all",) and yelp_records:
        build_few_shots(yelp_records, args.dry_run)

    if step in ("taxonomy", "all"):
        process_taxonomy(args.dry_run)

    if step in ("phrases", "all"):
        build_phrase_library(afrisenti_records, args.dry_run)

    elapsed = (datetime.now() - t0).total_seconds()
    _log(f"Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
