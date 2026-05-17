"""Eval metric — ROUGE-L.

Computes ROUGE-L (longest common subsequence) F1 score between
generated and reference reviews. Uses the ``rouge-score`` library.

Usage:
    from naijareview.eval.metrics.rouge import compute_rouge_l

    score = compute_rouge_l("This food dey sweet", "The food was delicious")
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_rouge_l(prediction: str, reference: str) -> float:
    """Compute ROUGE-L F1 score between prediction and reference.

    Args:
        prediction: The generated review text.
        reference: The ground-truth review text.

    Returns:
        ROUGE-L F1 score as a float in [0, 1], or 0.0 on error.
    """
    if not prediction or not reference:
        return 0.0

    try:
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, prediction)
        return float(scores["rougeL"].fmeasure)
    except ImportError:
        logger.warning("rouge-score not installed. Install with: pip install rouge-score")
        return 0.0
    except Exception as exc:
        logger.warning("ROUGE-L computation failed: %s", exc)
        return 0.0
