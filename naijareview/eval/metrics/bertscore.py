"""Eval metric — BERTScore.

Computes BERTScore F1 between generated and reference reviews.
Uses the ``bert-score`` library with ``roberta-large`` model.

Usage:
    from naijareview.eval.metrics.bertscore import compute_bert_score

    score = compute_bert_score("This food dey sweet", "The food was delicious")
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_bert_score(prediction: str, reference: str) -> float:
    """Compute BERTScore F1 between prediction and reference.

    Args:
        prediction: The generated review text.
        reference: The ground-truth review text.

    Returns:
        BERTScore F1 as a float in [0, 1], or 0.0 on error.
    """
    if not prediction or not reference:
        return 0.0

    try:
        import torch
        from bert_score import score as bert_score

        # bert_score.score returns (precision, recall, f1) tensors
        P, R, F1 = bert_score([prediction], [reference], lang="en", verbose=False)
        return float(F1[0])
    except ImportError:
        logger.warning("bert-score not installed. Install with: pip install bert-score")
        return 0.0
    except Exception as exc:
        logger.warning("BERTScore computation failed: %s", exc)
        return 0.0
