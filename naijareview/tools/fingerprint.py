"""Fingerprint tools: build_behavioural_fingerprint.

See §4.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.user import Fingerprint, UserHistory


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
    # TODO: Implement — Testimony owns FingerprintBuilder skill
    raise NotImplementedError("build_behavioural_fingerprint not yet implemented")
