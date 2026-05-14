"""Main evaluation orchestrator.

Owner: Aaliyah
See §12.1–12.5 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class HarnessConfig:
    """Configuration for the evaluation harness.

    Variants:
    - full: All components active
    - vibe_off: Naija Vibe Mode disabled
    - no_fingerprint: Average-user fingerprint used
    - no_persona: AfriSenti few-shots and region detection stripped
    - no_synthetic: Synthetic corpus excluded from training data
    """

    variant: Literal["full", "vibe_off", "no_fingerprint", "no_persona", "no_synthetic"] = "full"
    sample_size: int = 1000
    seed: int = 42


@dataclass
class TaskAResults:
    """Results from Task A evaluation."""

    rouge_l: float = 0.0
    bert_score: float = 0.0
    rating_mae: float = 0.0
    abeg_score_mean: float = 0.0
    sample_count: int = 0
    failure_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskBResults:
    """Results from Task B evaluation."""

    ndcg_at_10: float = 0.0
    hit_at_10: float = 0.0
    diversity_mean: float = 0.0
    abeg_score_mean: float = 0.0
    sample_count: int = 0
    failure_count: int = 0
    metadata: dict = field(default_factory=dict)


class EvalHarness:
    """Main evaluation orchestrator."""

    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    def run_task_a(self, variant: str = "full") -> TaskAResults:
        """Generate reviews for held-out users, score against ground truth."""
        # TODO: Implement
        raise NotImplementedError

    def run_task_b(self, variant: str = "full") -> TaskBResults:
        """Recommend items for held-out users, score against actual reviews."""
        # TODO: Implement
        raise NotImplementedError

    def run_ablation_sweep(self) -> dict:
        """Run all 5 variants and produce comparison table."""
        # TODO: Implement
        raise NotImplementedError
