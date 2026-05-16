"""Synthetic Nigerian review generation pipeline.

Generates review variants that serve BOTH tasks:
  Task A — review generation: synthetic reviews as few-shot references
  Task B — recommendation: review text used to describe items, inform ranking

Output schema is designed for:
  - Review Text Quality eval (ROUGE-L, BERTScore vs Yelp references)
  - Ranking Quality eval (NDCG@10, Hit@10 via user-item preference signals)
  - Rating Accuracy eval (|predicted_stars - actual| comparison)
  - Cross-domain generalisation (food, services, retail, health, entertainment)
  - Two evaluation modes:
      naija_mode=false → plain English, evaluated against standard Yelp metrics
      naija_mode=true  → Nigerian register, evaluated against Abeg score thresholds

Outputs:
  data/synthetic/nigerian_reviews.jsonl      — all generated reviews
  data/phrase_library/indexed_library.json   — (region × category × sentiment × register) index
  data/phrase_library/token_corpus.txt       — Pidgin token corpus for NaijaVibeChecker

Usage:
  python3 scripts/generate_synthetic_reviews.py
  python3 scripts/generate_synthetic_reviews.py --dry-run
  python3 scripts/generate_synthetic_reviews.py --step index
  python3 scripts/generate_synthetic_reviews.py --reset-checkpoint
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

from dotenv import load_dotenv

load_dotenv()

# ── Environment ───────────────────────────────────────────────────────────────

# def _load_env() -> None:
#     env_path = ROOT / ".env"
#     if not env_path.exists():
#         print("[WARN] .env not found. Copy .env.example and set GEMINI_API_KEY.")
#         return
#     for line in env_path.read_text().splitlines():
#         line = line.strip()
#         if line and not line.startswith("#") and "=" in line:
#             k, _, v = line.partition("=")
#             os.environ.setdefault(k.strip(), v.strip())


# _load_env()

# ── Paths ─────────────────────────────────────────────────────────────────────

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SYNTHETIC = ROOT / "data" / "synthetic"
PHRASE_LIB = ROOT / "data" / "phrase_library"
CHECKPOINT = SYNTHETIC / ".checkpoint.json"
OUTPUT_JSONL = SYNTHETIC / "nigerian_reviews.jsonl"

# ── Config ────────────────────────────────────────────────────────────────────

MODEL = "gemini-2.0-flash"
BASE_REVIEWS_PER_CALL = 2
AFRISENTI_EXAMPLES_PER_CALL = 3
CALL_DELAY_S = 0.6
MAX_RETRIES = 3

# Regions: 5 Nigerian + "general" (no region assumed, used for plain-English eval)
REGIONS = ["Lagos", "Abuja", "Port Harcourt", "Kano", "Enugu", "general"]
SENTIMENTS = ["positive", "negative", "neutral"]
SENTIMENT_TO_STARS = {"positive": "4 or 5", "negative": "1 or 2", "neutral": "3"}

# Registers map to naija_mode:
#   natural   → naija_mode=false (Nigerian English, light Pidgin — eval baseline)
#   amplified → naija_mode=true  (mixed English-Pidgin)
#   heavy     → naija_mode=true  (predominantly Pidgin, NaijaVibeChecker corpus)
REGISTER_DEFINITIONS = {
    "natural": (
        "Nigerian English with very light Pidgin — sounds like an educated Nigerian "
        "writing a standard English review. Occasional phrases like 'the food was really "
        "nice o' or 'I will definitely return'. Readable as plain English for evaluation purposes."
    ),
    "amplified": (
        "Mixed English-Pidgin — phrases like 'this place don sweet me die', "
        "'e get value for money', 'na here I go always patronize'. "
        "Pidgin constructs mix freely with English sentences."
    ),
    "heavy": (
        "Predominantly Pidgin — 'na so e be o', 'e don make sense', "
        "'I swear this food dey burst brain', 'oga na top tier be this'. "
        "Full Pidgin grammar. Feels like WhatsApp/Twitter Naija register."
    ),
}

REGION_SIGNALS = {
    "Lagos": "Naturally reference Lagos areas: VI, Lekki, Surulere, Ikeja, Yaba. Traffic/okada may appear.",
    "Abuja": "Naturally reference Abuja areas: Wuse, Maitama, Garki. Slightly more formal tone fits Abuja culture.",
    "Port Harcourt": "Naturally reference PH areas: GRA, Trans Amadi. PH slang, seafood/bole culture where relevant.",
    "Kano": "Naturally reference Kano landmarks: Sabon Gari, Nassarawa. Hausa loanwords: ranka dede, madalla.",
    "Enugu": "Naturally reference Enugu areas: Independence Layout, Ogui. Igbo loanwords: biko, nna, nne.",
    "general": "No specific region. Write as a Nigerian without revealing location. Universally understood Nigerian English.",
}

# Domain taxonomy for cross-domain generalisation.
# Maps nigerian_category → domain tag used in output + eval grouping.
CATEGORY_DOMAIN = {
    "Buka / Mama Put": "food",
    "Suya Joint / Street Food": "food",
    "Eateries (Mr Biggs-style)": "food",
    "Pepper Soup Spot": "food",
    "Beer Parlour": "food",
    "Canteen / Bukateria": "food",
    "Confectionery / Bakery": "food",
    "Open Market Stall": "retail",
    "Guesthouse / Lodge": "hospitality",
    "Beauty / Salon": "services",
}

# Yelp category equivalent for each Nigerian category (links synthetic to item index)
CATEGORY_YELP_EQUIV = {
    "Buka / Mama Put": "Restaurants",
    "Suya Joint / Street Food": "Barbeque",
    "Eateries (Mr Biggs-style)": "Fast Food",
    "Pepper Soup Spot": "African",
    "Beer Parlour": "Bars",
    "Canteen / Bukateria": "Cafes",
    "Confectionery / Bakery": "Bakeries",
    "Open Market Stall": "Shopping",
    "Guesthouse / Lodge": "Hotels & Travel",
    "Beauty / Salon": "Beauty & Spas",
}


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_taxonomy() -> dict:
    return json.loads((RAW / "nigerian_taxonomy.json").read_text())


def _load_few_shots_by_sentiment() -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    path = PROCESSED / "few_shots.jsonl"
    if not path.exists():
        print("[WARN] few_shots.jsonl missing — run process_data.py first")
        return by
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            by[r["sentiment"]].append(r)
    return dict(by)


def _load_afrisenti_by_label() -> dict[str, list[str]]:
    by: dict[str, list[str]] = defaultdict(list)
    path = PROCESSED / "pidgin_examples.jsonl"
    if not path.exists():
        print("[WARN] pidgin_examples.jsonl missing — run process_data.py first")
        return by
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    records.sort(key=lambda r: r["pidgin_density"], reverse=True)
    for r in records:
        by[r["label"]].append(r["text"])
    return dict(by)


# ── Checkpoint ────────────────────────────────────────────────────────────────

def _load_checkpoint() -> set[str]:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text()).get("completed", []))
    return set()


def _save_checkpoint(completed: set[str]) -> None:
    CHECKPOINT.write_text(json.dumps({"completed": sorted(completed)}, indent=2))


def _cell_key(region: str, category: str, sentiment: str) -> str:
    return f"{region}|{category}|{sentiment}"


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(
    region: str,
    nigerian_category: str,
    category_meta: dict,
    sentiment: str,
    base_reviews: list[str],
    afrisenti_examples: list[str],
) -> str:
    base_block = "\n\n".join(
        f"Reference {i+1} (real review — adapt style, do NOT copy):\n{t}"
        for i, t in enumerate(base_reviews)
    )
    pidgin_block = "\n".join(f"- {ex}" for ex in afrisenti_examples)
    keywords = ", ".join(category_meta.get("keywords", [])[:8])

    register_block = "\n".join(
        f'  "{r}": {desc}' for r, desc in REGISTER_DEFINITIONS.items()
    )

    stars_range = SENTIMENT_TO_STARS[sentiment]
    region_ctx = REGION_SIGNALS[region]

    return f"""You are a data generator building training and evaluation data for a Nigerian review AI.

## Task
Generate exactly 3 Nigerian-style reviews of a **{nigerian_category}** \
({category_meta.get("description", "")}).
Each review must use a different register: natural, amplified, heavy.
All 3 must express **{sentiment}** sentiment ({stars_range} stars).

## Registers
{register_block}

## Region context
{region_ctx}

## Yelp reference reviews (for writing style and topic ideas — do NOT copy verbatim)
{base_block}

## Authentic Nigerian Pidgin examples (for linguistic authenticity)
{pidgin_block}

## Category-specific keywords (use where natural)
{keywords}

## Quality rules — these reviews must pass evaluation on:
1. **Review Text Quality**: Each review must be coherent, grammatically consistent within its register, and opinion-rich. Avoid vague filler.
2. **Rating Accuracy**: Stars 1-2 = clearly negative experience, 3 = mixed/neutral, 4-5 = clearly positive. The review text must unambiguously support the star rating.
3. **Cross-domain signal**: Even though this is a {nigerian_category}, the review should contain transferable signals (quality, service, value, atmosphere) that work for recommendation ranking.
4. Length: 70-230 words per review.
5. No AI filler: no "I highly recommend", "exceptional experience", "must-visit", "overall".
6. Do NOT copy reference text verbatim. Do NOT mention Yelp.

## Output format
Return ONLY a valid JSON array. No markdown. No explanation. No code fences.

[
  {{
    "text": "...",
    "register": "natural",
    "stars": <int 1-5>
  }},
  {{
    "text": "...",
    "register": "amplified",
    "stars": <int 1-5>
  }},
  {{
    "text": "...",
    "register": "heavy",
    "stars": <int 1-5>
  }}
]"""


# ── LLM setup (plain invoke — no structured output to avoid schema issues) ───

def _make_llm(api_key: str):
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=MODEL,
        google_api_key=api_key,
        temperature=0.2
    )


# ── Response parsing ──────────────────────────────────────────────────────────

_PIDGIN_TOKENS = {
    "dey", "na", "dem", "abeg", "oga", "wahala", "sha", "sef", "nna", "wey",
    "chop", "belle", "abi", "shey", "wetin", "jollof", "suya", "egusi", "amala",
    "fufu", "buka", "nepa", "phcn", "ehen", "ehn", "oya", "naija", "sabi",
    "kuku", "biko", "nne", "madalla", "ranka", "chai", "tufiakwa", "gbese",
    "ghen", "nah", "correct", "e don", "no be", "na im",
}


def _pidgin_density(text: str) -> float:
    tokens = re.findall(r"[a-z']+", text.lower())
    if not tokens:
        return 0.0
    return round(sum(1 for t in tokens if t in _PIDGIN_TOKENS) / len(tokens), 4)


def _parse_llm_response(
    raw: str,
    region: str,
    nigerian_category: str,
    sentiment: str,
) -> list[dict]:
    """Extract and validate reviews from plain-text LLM response."""
    # Strip any accidental code fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")

    # Find the JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []

    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    valid = []
    seen_registers: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        text = str(item.get("text", "")).strip()
        reg = str(item.get("register", "")).strip()
        stars = item.get("stars")

        if len(text) < 50 or reg not in REGISTER_DEFINITIONS:
            continue
        if reg in seen_registers:
            continue
        if not isinstance(stars, int) or not (1 <= stars <= 5):
            stars = {"positive": 4, "negative": 2, "neutral": 3}[sentiment]

        seen_registers.add(reg)
        density = _pidgin_density(text)

        valid.append({
            "review_id": f"syn_{region.lower().replace(' ', '_')}_{nigerian_category[:8].lower().replace('/', '_').replace(' ', '_')}_{sentiment[:3]}_{reg[:3]}_{len(valid)}",
            "text": text,
            "stars": stars,
            "sentiment": sentiment,
            "register": reg,
            # naija_mode: natural is English-eval-compatible; amplified/heavy activate Naija pipeline
            "naija_mode": reg != "natural",
            "category": nigerian_category,
            "yelp_category": CATEGORY_YELP_EQUIV.get(nigerian_category, "Restaurants"),
            "domain": CATEGORY_DOMAIN.get(nigerian_category, "general"),
            "region": region,
            "pidgin_density": density,
            "text_len": len(text),
            "source": "synthetic",
            # eval flags — used by eval harness to select correct metric suite
            "eval_text_quality": True,       # ROUGE / BERTScore eligible
            "eval_rating_accuracy": True,    # star prediction comparison
            "eval_cross_domain": reg == "natural",  # cross-domain eval only on plain register
        })

    return valid


# ── Generation loop ───────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_generation(dry_run: bool) -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not dry_run:
        print("ERROR: GEMINI_API_KEY not set. Add it to .env")
        sys.exit(1)
    if api_key.startswith("AIza-xxx") or api_key == "AIza-xxxxx":
        print("ERROR: GEMINI_API_KEY is still the placeholder. Replace it in .env with your real key.")
        sys.exit(1)

    taxonomy = _load_taxonomy()
    few_shots = _load_few_shots_by_sentiment()
    afrisenti = _load_afrisenti_by_label()
    categories = taxonomy.get("mappings", [])
    completed = _load_checkpoint()

    remaining = [
        (region, cat, sentiment)
        for region in REGIONS
        for cat in categories
        for sentiment in SENTIMENTS
        if _cell_key(region, cat["nigerian_category"], sentiment) not in completed
    ]

    total_cells = len(REGIONS) * len(categories) * len(SENTIMENTS)
    _log(f"Plan: {total_cells} cells, {len(remaining)} remaining, {len(completed)} done")
    _log(f"Target: ~{len(remaining) * 3} reviews (3 per cell: natural/amplified/heavy)")

    if dry_run:
        _log("DRY RUN — no LLM calls")
        print("\nSample cells:")
        for region, cat, sentiment in remaining[:6]:
            key = _cell_key(region, cat["nigerian_category"], sentiment)
            domain = CATEGORY_DOMAIN.get(cat["nigerian_category"], "general")
            print(f"  {key}  [domain={domain}]")
        return

    SYNTHETIC.mkdir(parents=True, exist_ok=True)
    llm = _make_llm(api_key)
    generated_total = 0
    failed_cells: list[str] = []

    with open(OUTPUT_JSONL, "a", encoding="utf-8") as out_f:
        for i, (region, cat_meta, sentiment) in enumerate(remaining):
            nigerian_category = cat_meta["nigerian_category"]
            cell_key = _cell_key(region, nigerian_category, sentiment)

            pool = few_shots.get(sentiment, [])
            base_reviews = [
                r["text"][:700]
                for r in random.sample(pool, min(BASE_REVIEWS_PER_CALL, len(pool)))
            ]
            afri_pool = afrisenti.get(sentiment, [])
            afri_examples = afri_pool[:AFRISENTI_EXAMPLES_PER_CALL]

            prompt = _build_prompt(
                region=region,
                nigerian_category=nigerian_category,
                category_meta=cat_meta,
                sentiment=sentiment,
                base_reviews=base_reviews,
                afrisenti_examples=afri_examples,
            )

            _log(f"[{i+1}/{len(remaining)}] {region} / {nigerian_category} / {sentiment}")

            for attempt in range(MAX_RETRIES):
                try:
                    from langchain_core.messages import HumanMessage
                    response = llm.invoke([HumanMessage(content=prompt)])
                    raw = str(response.content)

                    records = _parse_llm_response(raw, region, nigerian_category, sentiment)

                    if not records:
                        _log(f"  WARN: parse failed — raw snippet: {raw[:120]!r}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(1)
                            continue
                        failed_cells.append(cell_key)
                    else:
                        for rec in records:
                            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        out_f.flush()
                        generated_total += len(records)
                        completed.add(cell_key)
                        _save_checkpoint(completed)
                        densities = [round(r["pidgin_density"], 3) for r in records]
                        registers = [r["register"] for r in records]
                        _log(f"  OK: {len(records)} reviews | registers={registers} | pidgin={densities}")
                    break

                except Exception as exc:
                    err_str = str(exc)
                    is_retryable = any(x in err_str.lower() for x in ("429", "quota", "rate", "500", "503", "timeout"))

                    if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                        print("\nERROR: API key is invalid. Check GEMINI_API_KEY in your .env file.")
                        sys.exit(1)

                    if is_retryable and attempt < MAX_RETRIES - 1:
                        wait = 2 ** (attempt + 1)
                        _log(f"  Retryable error — waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
                        time.sleep(wait)
                    else:
                        _log(f"  ERROR [{type(exc).__name__}]: {err_str[:200]}")
                        failed_cells.append(cell_key)
                        break

            time.sleep(CALL_DELAY_S)

    _log(f"\nGeneration complete: {generated_total} reviews written")
    if failed_cells:
        _log(f"Failed ({len(failed_cells)} cells): {failed_cells[:10]}")
        _log("Re-run the script to retry failed cells (checkpoint skips successful ones).")


# ── Phrase library indexer ────────────────────────────────────────────────────

def build_indexed_library() -> None:
    """Build phrase library indexed by (region, sentiment, category, register).

    Index structure serves fetch_few_shot_examples(region, sentiment, category, k):
    {
      "Lagos": {
        "positive": {
          "Buka / Mama Put": {
            "natural": ["...", ...],   ← naija_mode=false few-shots
            "amplified": ["...", ...], ← naija_mode=true few-shots
            "heavy": ["...", ...]      ← NaijaVibeChecker corpus
          },
          "*": { ... }                 ← wildcard fallback (any category)
        }
      }
    }
    """
    _log("Building indexed phrase library…")

    records: list[dict] = []
    if OUTPUT_JSONL.exists():
        with open(OUTPUT_JSONL) as f:
            for line in f:
                records.append(json.loads(line))

    if not records:
        _log("WARN: no synthetic reviews found. Run generation step first.")
        return

    # Sort richest Pidgin first so callers get best examples on slice [:k]
    records.sort(key=lambda r: r["pidgin_density"], reverse=True)

    index: dict = {}
    for rec in records:
        region = rec.get("region", "general")
        sentiment = rec.get("sentiment", "neutral")
        category = rec.get("category", "unknown")
        register = rec.get("register", "natural")
        text = rec.get("text", "")

        index.setdefault(region, {})
        index[region].setdefault(sentiment, {})
        index[region][sentiment].setdefault(category, {})
        index[region][sentiment][category].setdefault(register, [])
        index[region][sentiment][category][register].append(text)

    # Build wildcard (*) fallback per (region, sentiment)
    for region in index:
        for sentiment in index[region]:
            all_by_reg: dict[str, list[str]] = defaultdict(list)
            for cat, regs in index[region][sentiment].items():
                if cat == "*":
                    continue
                for reg, texts in regs.items():
                    all_by_reg[reg].extend(texts)
            index[region][sentiment]["*"] = {
                reg: list(dict.fromkeys(txts))[:20]
                for reg, txts in all_by_reg.items()
            }

    total = sum(
        len(texts)
        for r in index.values()
        for s in r.values()
        for cat, regs in s.items()
        if cat != "*"
        for texts in regs.values()
    )
    _log(f"Indexed {total} reviews across {len(index)} regions")
    for region, sentiments in index.items():
        count = sum(
            len(texts)
            for s in sentiments.values()
            for cat, regs in s.items()
            if cat != "*"
            for texts in regs.values()
        )
        _log(f"  {region}: {count}")

    PHRASE_LIB.mkdir(parents=True, exist_ok=True)
    out = PHRASE_LIB / "indexed_library.json"
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    _log(f"Wrote {out.relative_to(ROOT)}")

    _build_token_corpus(records)


def _build_token_corpus(records: list[dict]) -> None:
    STOP_WORDS = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should", "this",
        "that", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his",
        "its", "our", "their", "and", "but", "or", "for", "in", "on", "at", "by",
        "to", "of", "up", "as", "with", "from", "not", "no", "very", "good",
        "great", "nice", "bad", "food", "place", "service", "get", "go", "come",
        "here", "there", "all", "also", "more", "than", "then", "really", "just",
        "time", "one", "new", "even", "back",
    }
    freq: dict[str, int] = defaultdict(int)

    for rec in records:
        if rec.get("register") in ("amplified", "heavy"):
            for tok in re.findall(r"[a-z']+", rec.get("text", "").lower()):
                freq[tok] += 1

    ex_path = PHRASE_LIB / "examples_by_sentiment.json"
    if ex_path.exists():
        for texts in json.loads(ex_path.read_text()).values():
            for text in texts:
                for tok in re.findall(r"[a-z']+", text.lower()):
                    freq[tok] += 1

    tokens = sorted(
        ((tok, cnt) for tok, cnt in freq.items()
         if cnt >= 3 and tok not in STOP_WORDS and len(tok) >= 2),
        key=lambda kv: kv[1], reverse=True,
    )
    out = PHRASE_LIB / "token_corpus.txt"
    out.write_text("\n".join(f"{tok}\t{cnt}" for tok, cnt in tokens))
    _log(f"Token corpus: {len(tokens)} Pidgin tokens → {out.relative_to(ROOT)}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--step", choices=["generate", "index", "all"], default="all")
    parser.add_argument("--reset-checkpoint", action="store_true")
    args = parser.parse_args()

    if args.reset_checkpoint and CHECKPOINT.exists():
        CHECKPOINT.unlink()
        _log("Checkpoint cleared")

    if args.step in ("generate", "all"):
        run_generation(args.dry_run)

    if args.step in ("index", "all") and not args.dry_run:
        build_indexed_library()

    _log("Done")


if __name__ == "__main__":
    main()
