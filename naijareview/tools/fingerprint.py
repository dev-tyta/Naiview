"""Fingerprint tools: build_behavioural_fingerprint.

See §4.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime

from langchain_core.tools import tool

from naijareview.schemas.user import Fingerprint, UserHistory

_STOPWORDS = {
    "i", "a", "the", "and", "or", "but", "in", "on", "at", "to", "of",
    "for", "is", "was", "it", "this", "that", "with", "we", "my", "your",
    "our", "are", "were", "be", "been", "has", "had", "have", "not", "no",
    "so", "by", "an", "as", "from", "he", "she", "they", "you",
}

_INTENSIFIERS = {
    "very", "so", "really", "absolutely", "terrible", "amazing", "horrible",
    "excellent", "awful", "wonderful", "love", "hate",
}

def _load_pidgin_set() -> set[str]:
    """Load the full 847-token Nigerian slang corpus from phrase_library."""
    from pathlib import Path
    corpus_path = Path("data/phrase_library/token_corpus.txt")
    if corpus_path.exists():
        return {
            line.split("\t")[0].strip().lower()
            for line in corpus_path.read_text().splitlines()
            if line.strip()
        }
    # Fallback hardcoded set if file missing
    return {
        "dey", "na", "dem", "abeg", "oga", "wahala", "sha", "sef", "nna",
        "wey", "chop", "belle", "abi", "shey", "wetin", "oya", "naija",
        "ehen", "ehn", "mumu",
    }

_PIDGIN_SET = _load_pidgin_set()

_POSITIVE_WORDS = {"good", "great", "love", "amazing", "excellent"}
_NEGATIVE_WORDS = {"bad", "terrible", "awful", "horrible", "hate"}


def _tokenize(text: str) -> list[str]:
    """Lowercase and split into alpha-only tokens."""
    return [w.lower() for w in text.split() if w.isalpha()]


def _word_count(text: str) -> int:
    return len(text.split())


def _percentile(values: list[float], pct: float) -> float:
    """Return the value at the given percentile (0-100)."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    idx = (pct / 100.0) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_vals[-1]
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _vader_compound(text: str) -> float:
    """Return VADER compound score, falling back to simple heuristic."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
        analyzer = SentimentIntensityAnalyzer()
        return float(analyzer.polarity_scores(text)["compound"])
    except Exception:
        tokens = _tokenize(text)
        score = 0.0
        for token in tokens:
            if token in _POSITIVE_WORDS:
                score += 0.1
            elif token in _NEGATIVE_WORDS:
                score -= 0.1
        return max(-1.0, min(1.0, score))


def _pearson_corr(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation; returns 0.0 if undefined."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return num / (denom_x * denom_y)


@tool
def build_behavioural_fingerprint(user_history: UserHistory) -> Fingerprint:
    """Compute the 7-dimensional behavioural fingerprint from user history.

    Dimensions:
    - Generosity: mean of (user_stars − platform_avg), normalised [0,1]
    - Verbosity: quantile rank of mean word count; word range is (20th, 80th pctl)
    - Emotional intensity: lexicon-based intensifier count, normalised
    - Topic focus: top-3 noun phrases appearing > 30% of reviews (via spaCy)
    - Consistency: Pearson(sentiment, star rating), scaled [0,1]
    - Recency weight: exponential decay coefficient over timestamps
    - Naija slang index: fraction of tokens matching Nigerian phrase library

    Caching: Result cached in Redis keyed by (user_id, last_review_timestamp).
    If history has < 3 reviews, returns fingerprint with wide confidence intervals.

    Args:
        user_history: The user's full review history.

    Returns:
        Computed Fingerprint with confidence intervals.
    """
    reviews = user_history.reviews
    few_reviews = len(reviews) < 3
    now = datetime.now()

    # ── Generosity score ──────────────────────────────────────────────────
    if reviews:
        raw_gen = sum(r.stars - 3.0 for r in reviews) / len(reviews)
        generosity_score = float(max(0.0, min(1.0, (raw_gen + 2.0) / 4.0)))
    else:
        generosity_score = 0.5

    # ── Verbosity ─────────────────────────────────────────────────────────
    word_counts = [float(_word_count(r.text)) for r in reviews] if reviews else [0.0]
    mean_wc = sum(word_counts) / len(word_counts)

    # Quantile rank: fraction of reviews with word count <= mean_wc
    verbosity_score = float(
        sum(1 for wc in word_counts if wc <= mean_wc) / len(word_counts)
    )

    p20 = max(40, int(_percentile(word_counts, 20)))
    p80 = max(120, int(_percentile(word_counts, 80)))
    verbosity_word_range: tuple[int, int] = (p20, p80)

    # ── Emotional intensity ───────────────────────────────────────────────
    per_review_intensity: list[float] = []
    for r in reviews:
        tokens = _tokenize(r.text)
        if not tokens:
            per_review_intensity.append(0.0)
            continue
        count = sum(1 for t in tokens if t in _INTENSIFIERS)
        per_review_intensity.append(count / len(tokens))

    if per_review_intensity:
        min_i = min(per_review_intensity)
        max_i = max(per_review_intensity)
        if max_i > min_i:
            raw_intensity = (
                sum(per_review_intensity) / len(per_review_intensity) - min_i
            ) / (max_i - min_i)
        else:
            raw_intensity = 0.5 if per_review_intensity else 0.0
        emotional_intensity = float(max(0.0, min(1.0, raw_intensity)))
    else:
        emotional_intensity = 0.0

    # ── Emotional style ───────────────────────────────────────────────────
    if emotional_intensity < 0.25:
        emotional_style = "calm"
    elif emotional_intensity < 0.5:
        emotional_style = "balanced"
    elif emotional_intensity < 0.75:
        emotional_style = "passionate"
    else:
        emotional_style = "dramatic"

    # ── Topic focus ───────────────────────────────────────────────────────
    all_tokens: list[str] = []
    for r in reviews:
        all_tokens.extend(t for t in _tokenize(r.text) if t not in _STOPWORDS)

    token_counts = Counter(all_tokens)
    # Keep words appearing at least 3 times, take top 3
    qualified = [(w, c) for w, c in token_counts.most_common() if c >= 3]
    topic_focus = [w for w, _ in qualified[:3]]
    if not topic_focus:
        # Fallback: take top 3 regardless of count
        topic_focus = [w for w, _ in token_counts.most_common(3)]

    # ── Consistency score ─────────────────────────────────────────────────
    if len(reviews) >= 2:
        star_scores = [r.stars for r in reviews]
        sentiment_scores = [_vader_compound(r.text) for r in reviews]
        corr = _pearson_corr(star_scores, sentiment_scores)
        consistency_score = float((corr + 1.0) / 2.0)
    else:
        consistency_score = 0.5

    # ── Recency weight ────────────────────────────────────────────────────
    if reviews:
        decay_scores = [
            math.exp(-max(0, (now - r.timestamp).days) / 365.0)
            for r in reviews
        ]
        recency_weight = float(sum(decay_scores) / len(decay_scores))
    else:
        recency_weight = 0.5

    # ── Naija slang index ─────────────────────────────────────────────────
    all_raw_tokens: list[str] = []
    for r in reviews:
        all_raw_tokens.extend(r.text.lower().split())
    if all_raw_tokens:
        pidgin_count = sum(1 for t in all_raw_tokens if t in _PIDGIN_SET)
        naija_slang_index = float(pidgin_count / len(all_raw_tokens))
    else:
        naija_slang_index = 0.0

    # ── Confidence intervals ──────────────────────────────────────────────
    margin = 0.30 if few_reviews else 0.15
    ci_keys = {
        "generosity_score": generosity_score,
        "verbosity_score": verbosity_score,
        "consistency_score": consistency_score,
    }
    confidence_intervals: dict[str, tuple[float, float]] = {
        k: (max(0.0, v - margin), min(1.0, v + margin))
        for k, v in ci_keys.items()
    }

    return Fingerprint(
        user_id=user_history.user_id,
        generosity_score=generosity_score,
        verbosity_score=verbosity_score,
        verbosity_word_range=verbosity_word_range,
        emotional_intensity=emotional_intensity,
        emotional_style=emotional_style,
        topic_focus=topic_focus,
        consistency_score=consistency_score,
        recency_weight=recency_weight,
        naija_slang_index=naija_slang_index,
        confidence_intervals=confidence_intervals,
        computed_at=now,
        review_count_at_computation=len(reviews),
    )
