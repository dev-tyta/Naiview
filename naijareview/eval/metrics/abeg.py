"""Eval metric — Abeg score (batch evaluation wrapper).

Computes the Abeg Score (cultural authenticity composite) for generated
reviews using the NaijaVibeChecker in passive mode.

Formula: 0.4 × cultural_authenticity + 0.35 × cultural_accuracy
         + 0.25 × persona_consistency

Usage:
    from naijareview.eval.metrics.abeg import compute_abeg_batch

    scores = compute_abeg_batch(reviews, fingerprints, items)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_abeg_batch(
    reviews: list[str],
    fingerprints: list[Any],
    items: list[Any],
) -> list[float]:
    """Compute Abeg scores for a batch of reviews using NaijaVibeChecker.

    Each review is scored in passive mode — results are informational,
    no regeneration is triggered.

    Args:
        reviews: List of generated review texts.
        fingerprints: List of Fingerprint objects (parallel to reviews).
        items: List of Item objects (parallel to reviews).

    Returns:
        List of Abeg scores in [0, 1], one per review. Returns 0.0 for
        any review that fails to score.
    """
    if not reviews:
        return []

    try:
        from naijareview.llm.router import LLMRouter
        from naijareview.skills.vibe_checking import NaijaVibeChecker

        checker = NaijaVibeChecker(
            llm_router=LLMRouter(),
            phrase_library=None,  # Loaded internally by the tool
        )

        scores: list[float] = []
        for review, fp, item in zip(reviews, fingerprints, items):
            try:
                vibe = checker.score(
                    review_text=review,
                    fingerprint=fp,
                    item=item,
                    mode="passive",
                )
                scores.append(float(vibe.abeg_score))
            except Exception as exc:
                logger.warning("Abeg scoring failed for a review: %s", exc)
                scores.append(0.0)

        return scores

    except ImportError as exc:
        logger.warning("Abeg scoring unavailable: %s", exc)
        return [0.0] * len(reviews)
    except Exception as exc:
        logger.warning("Abeg batch scoring failed: %s", exc)
        return [0.0] * len(reviews)
