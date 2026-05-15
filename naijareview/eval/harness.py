"""
NaijaReview Intelligence — Eval Harness Skeleton
Unblocker: stub agents plug in immediately; real agents implement AgentProtocol.

Usage:
    python -m naijareview.eval.harness --task A --agent stub
    python -m naijareview.eval.harness --task B --agent real --agent-module naijareview.agents.task_a
"""

from __future__ import annotations

import argparse
import importlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

# ── Harness Config (ablation support) ─────────────────────────────────────────


@dataclass
class HarnessConfig:
    """Configuration for ablation / variant sweeps.

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


# ── Data Contracts ────────────────────────────────────────────────────────────


@dataclass
class TaskAInput:
    user_id: str
    item_id: str
    item_metadata: dict[str, Any]
    user_history: list[dict[str, Any]]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAOutput:
    generated_review: str
    predicted_rating: float  # 1.0 – 5.0
    confidence: float  # 0 – 1
    fingerprint_match: str = ""
    style_notes: str = ""
    abeg_score: float | None = None
    latency_ms: float = 0.0


@dataclass
class TaskAStats:
    """Aggregated results from a Task A evaluation run."""

    rouge_l: float = 0.0
    bert_score: float = 0.0
    rating_mae: float = 0.0
    abeg_score_mean: float = 0.0
    sample_count: int = 0
    failure_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskBInput:
    user_id: str
    query: str
    user_history: list[dict[str, Any]]
    candidate_pool: list[dict[str, Any]]
    is_cold_start: bool = False
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskBOutput:
    recommendations: list[dict[str, Any]]
    reasoning: str
    confidence: float
    cold_start_mode: bool = False
    diversity_score: float = 0.0
    clarifying_question: str | None = None
    latency_ms: float = 0.0


@dataclass
class TaskBStats:
    """Aggregated results from a Task B evaluation run."""

    ndcg_at_10: float = 0.0
    hit_at_10: float = 0.0
    diversity_mean: float = 0.0
    abeg_score_mean: float = 0.0
    sample_count: int = 0
    failure_count: int = 0
    metadata: dict = field(default_factory=dict)


# ── Agent Protocol ────────────────────────────────────────────────────────────


class AgentProtocol(ABC):
    @abstractmethod
    def run_task_a(self, inp: TaskAInput) -> TaskAOutput: ...
    @abstractmethod
    def run_task_b(self, inp: TaskBInput) -> TaskBOutput: ...


# ── Stub Agents ───────────────────────────────────────────────────────────────


class StubAgent(AgentProtocol):
    """Schema-valid dummy outputs — keeps the harness green before real logic exists."""

    def run_task_a(self, inp: TaskAInput) -> TaskAOutput:
        return TaskAOutput(
            generated_review="[STUB] This place dey try sha. Abeg make dem improve.",
            predicted_rating=3.5,
            confidence=0.0,
            fingerprint_match="STUB — no real fingerprint yet",
            style_notes="STUB output",
        )

    def run_task_b(self, inp: TaskBInput) -> TaskBOutput:
        return TaskBOutput(
            recommendations=[
                {"item_id": "stub_001", "name": "[STUB] Mama Titi Kitchen", "score": 0.9},
                {"item_id": "stub_002", "name": "[STUB] Iya Basira Buka", "score": 0.8},
            ],
            reasoning="[STUB] No real reasoning yet.",
            confidence=0.0,
            cold_start_mode=inp.is_cold_start,
        )


# ── Metrics Registry ──────────────────────────────────────────────────────────


class MetricsRegistry:
    """
    All scorers live here. Replace each stub lambda with real implementation.
    Each scorer fn signature: (output, ground_truth) -> float
    """

    TASK_A_METRICS = {
        "rouge_l": lambda out, gt: 0.0,  # TODO: wire rouge-score lib
        "bert_score_f1": lambda out, gt: 0.0,  # TODO: wire bert-score lib
        "rating_mae": lambda out, gt: abs(out.predicted_rating - gt["rating"]),
        "abeg_score": lambda out, gt: out.abeg_score or 0.0,
    }

    TASK_B_METRICS = {
        "ndcg_at_10": lambda out, gt: 0.0,  # TODO
        "hit_rate_at_5": lambda out, gt: 0.0,  # TODO
        "diversity_score": lambda out, gt: out.diversity_score,
        "cold_start_hit": lambda out, gt: float(
            out.cold_start_mode and len(out.recommendations) > 0
        ),
    }

    @classmethod
    def score_task_a(cls, output: TaskAOutput, ground_truth: dict) -> dict[str, float]:
        return {k: fn(output, ground_truth) for k, fn in cls.TASK_A_METRICS.items()}

    @classmethod
    def score_task_b(cls, output: TaskBOutput, ground_truth: dict) -> dict[str, float]:
        return {k: fn(output, ground_truth) for k, fn in cls.TASK_B_METRICS.items()}


# ── Harness Runner ────────────────────────────────────────────────────────────


class EvalHarness:
    def __init__(
        self,
        agent: AgentProtocol,
        config: HarnessConfig | None = None,
        results_dir: str = "eval_results",
    ):
        self.agent = agent
        self.config = config or HarnessConfig()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_task_a(self, examples: list[dict]) -> dict:
        results, all_scores = [], []
        failures = 0

        for ex in examples:
            inp = TaskAInput(**ex["input"])
            t0 = time.perf_counter()
            try:
                out = self.agent.run_task_a(inp)
                out.latency_ms = (time.perf_counter() - t0) * 1000
            except Exception as e:
                failures += 1
                results.append({"input": ex["input"], "error": str(e)})
                continue

            scores = MetricsRegistry.score_task_a(out, ex.get("ground_truth", {}))
            results.append({"input": ex["input"], "output": asdict(out), "scores": scores})
            all_scores.append(scores)

        summary = self._aggregate(all_scores) if all_scores else {}
        summary["failure_count"] = failures
        summary["sample_count"] = len(examples)

        report = {
            "task": "A",
            "n": len(examples),
            "variant": self.config.variant,
            "summary": summary,
            "results": results,
        }
        self._save(report, "task_a")
        return report

    def run_task_b(self, examples: list[dict]) -> dict:
        results, all_scores = [], []
        failures = 0

        for ex in examples:
            inp = TaskBInput(**ex["input"])
            t0 = time.perf_counter()
            try:
                out = self.agent.run_task_b(inp)
                out.latency_ms = (time.perf_counter() - t0) * 1000
            except Exception as e:
                failures += 1
                results.append({"input": ex["input"], "error": str(e)})
                continue

            scores = MetricsRegistry.score_task_b(out, ex.get("ground_truth", {}))
            results.append({"input": ex["input"], "output": asdict(out), "scores": scores})
            all_scores.append(scores)

        summary = self._aggregate(all_scores) if all_scores else {}
        summary["failure_count"] = failures
        summary["sample_count"] = len(examples)

        report = {
            "task": "B",
            "n": len(examples),
            "variant": self.config.variant,
            "summary": summary,
            "results": results,
        }
        self._save(report, "task_b")
        return report

    def run_ablation_sweep(self, examples_a: list[dict], examples_b: list[dict]) -> dict:
        """Run all 5 variants and produce a comparison table."""
        variants = ["full", "vibe_off", "no_fingerprint", "no_persona", "no_synthetic"]
        results: dict[str, dict] = {}
        for v in variants:
            self.config.variant = v  # type: ignore[assignment]
            results[v] = {
                "task_a": self.run_task_a(examples_a)["summary"],
                "task_b": self.run_task_b(examples_b)["summary"],
            }
        sweep_report = {"variants": results}
        self._save(sweep_report, "ablation_sweep")
        return sweep_report

    def _aggregate(self, scores: list[dict[str, float]]) -> dict[str, float]:
        if not scores:
            return {}
        keys = list(scores[0].keys())
        return {k: sum(s[k] for s in scores) / len(scores) for k in keys}

    def _save(self, report: dict, tag: str):
        path = self.results_dir / f"{tag}_{int(time.time())}.json"
        path.write_text(json.dumps(report, indent=2, default=str))
        print(f"[harness] results saved → {path}")


# ── Fixture loader (drop JSON files in eval/fixtures/) ───────────────────────


def load_fixtures(task: str) -> list[dict]:
    fixture_dir = Path(__file__).parent / "fixtures"
    path = fixture_dir / f"task_{task.lower()}.json"
    if path.exists():
        return json.loads(path.read_text())
    # Fallback: one minimal synthetic example so harness always runs
    if task.upper() == "A":
        return [
            {
                "input": {
                    "user_id": "u001",
                    "item_id": "i001",
                    "item_metadata": {
                        "name": "Mama Put Kitchen",
                        "category": "Nigerian",
                        "location": "Lagos",
                    },
                    "user_history": [
                        {"review_text": "E sweet well well", "rating": 5, "item_id": "i000"}
                    ],
                },
                "ground_truth": {"rating": 4.0, "review_text": "Very good local food"},
            }
        ]
    return [
        {
            "input": {
                "user_id": "u001",
                "query": "good local food near me",
                "user_history": [
                    {"review_text": "E sweet well well", "rating": 5, "item_id": "i000"}
                ],
                "candidate_pool": [
                    {"item_id": "i001", "name": "Mama Put Kitchen"},
                    {"item_id": "i002", "name": "Iya Basira Buka"},
                ],
            },
            "ground_truth": {"relevant_ids": ["i001"]},
        }
    ]


# ── CLI ───────────────────────────────────────────────────────────────────────


def resolve_agent(name: str, module_path: str | None) -> AgentProtocol:
    if name == "stub":
        return StubAgent()
    if module_path:
        mod = importlib.import_module(module_path)
        return mod.Agent()  # each real agent module exposes Agent()
    raise ValueError(f"Unknown agent '{name}'. Pass --agent-module for real agents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NaijaReview Intelligence — Eval Harness")
    parser.add_argument("--task", required=True, choices=["A", "B", "both", "sweep"])
    parser.add_argument("--agent", default="stub")
    parser.add_argument("--agent-module", default=None)
    parser.add_argument(
        "--variant",
        default="full",
        choices=["full", "vibe_off", "no_fingerprint", "no_persona", "no_synthetic"],
    )
    parser.add_argument("--results-dir", default="eval_results")
    args = parser.parse_args()

    agent = resolve_agent(args.agent, args.agent_module)
    config = HarnessConfig(variant=args.variant)  # type: ignore[arg-type]
    harness = EvalHarness(agent, config=config, results_dir=args.results_dir)

    if args.task == "sweep":
        fa = load_fixtures("A")
        fb = load_fixtures("B")
        report = harness.run_ablation_sweep(fa, fb)
        print(f"[Sweep] complete across {len(report['variants'])} variants")
    else:
        if args.task in ("A", "both"):
            report = harness.run_task_a(load_fixtures("A"))
            print(f"[Task A] summary: {report['summary']}")

        if args.task in ("B", "both"):
            report = harness.run_task_b(load_fixtures("B"))
            print(f"[Task B] summary: {report['summary']}")
