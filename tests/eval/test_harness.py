"""Pytest wrapper for the evaluation harness.

Fast smoke tests (--dry-run) run in CI.
Full eval runs are invoked directly via:
    python tests/eval/harness.py --ablation --sample 100

Mark: @pytest.mark.eval  — excluded from default CI run via pytest.ini.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tests.eval.harness import (
    EvalConfig,
    AblationReport,
    build_held_out_set,
    compute_ndcg_at_k,
    compute_hit_at_k,
    compute_rouge_l,
    compute_rating_mae,
    bootstrap_ci,
    load_dataset,
    run_task_a_eval,
    run_task_b_eval,
    DATASET_PATH,
    RESULTS_DIR,
)


# ── Unit tests for metric functions (always run) ───────────────────────────────


class TestMetrics:
    def test_rouge_l_identical(self):
        assert compute_rouge_l("hello world", "hello world") == pytest.approx(1.0, abs=1e-6)

    def test_rouge_l_empty(self):
        assert compute_rouge_l("", "hello world") == 0.0

    def test_rouge_l_partial(self):
        score = compute_rouge_l("hello there", "hello world friend")
        assert 0.0 < score < 1.0

    def test_rating_mae(self):
        assert compute_rating_mae(4.0, 3.0) == pytest.approx(1.0)
        assert compute_rating_mae(3.5, 3.5) == pytest.approx(0.0)

    def test_ndcg_hit_at_k(self):
        ranked = ["item_a", "item_b", "item_target", "item_c"]
        relevant = {"item_target"}
        assert compute_hit_at_k(ranked, relevant, k=10) == 1.0
        assert compute_hit_at_k(ranked, relevant, k=2) == 0.0
        ndcg = compute_ndcg_at_k(ranked, relevant, k=10)
        assert 0.0 < ndcg < 1.0

    def test_ndcg_perfect(self):
        ranked = ["target"]
        relevant = {"target"}
        assert compute_ndcg_at_k(ranked, relevant, k=10) == pytest.approx(1.0)

    def test_bootstrap_ci_stable(self):
        vals = [0.5] * 100
        lo, hi = bootstrap_ci(vals, seed=42)
        assert lo == pytest.approx(0.5, abs=1e-3)
        assert hi == pytest.approx(0.5, abs=1e-3)

    def test_bootstrap_ci_nonempty(self):
        vals = [0.1, 0.5, 0.9, 0.3, 0.7]
        lo, hi = bootstrap_ci(vals, seed=42)
        assert lo <= hi
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0


# ── Dataset tests (always run if dataset present) ──────────────────────────────


@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset not present")
class TestDataset:
    def test_dataset_loads(self):
        records = load_dataset()
        assert len(records) > 1000
        assert "user_id" in records[0]
        assert "text" in records[0]
        assert "stars" in records[0]

    def test_held_out_set_construction(self):
        records = load_dataset()
        held_out = build_held_out_set(records, sample_size=20, seed=42, min_reviews=5)
        assert len(held_out) == 20
        for item in held_out:
            assert "user_id" in item
            assert "history" in item
            assert "target" in item
            assert len(item["history"]) >= 4  # min_reviews - 1

    def test_held_out_reproducible(self):
        records = load_dataset()
        a = build_held_out_set(records, sample_size=10, seed=42)
        b = build_held_out_set(records, sample_size=10, seed=42)
        assert [x["user_id"] for x in a] == [x["user_id"] for x in b]

    def test_held_out_different_seed(self):
        records = load_dataset()
        a = build_held_out_set(records, sample_size=10, seed=42)
        b = build_held_out_set(records, sample_size=10, seed=99)
        # Different seeds should (very likely) produce different sets
        assert [x["user_id"] for x in a] != [x["user_id"] for x in b]


# ── Dry-run smoke tests (no LLM, always run) ───────────────────────────────────


@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset not present")
class TestDryRun:
    """Validates harness logic without LLM calls."""

    def test_task_a_dry_run(self, tmp_path):
        records = load_dataset()
        eval_set = build_held_out_set(records, sample_size=5, seed=42)
        config = EvalConfig(
            variant="full",
            sample_size=5,
            seed=42,
            task="a",
            output_dir=tmp_path,
            dry_run=True,
        )
        results = run_task_a_eval(config, eval_set)
        assert results.n == 5
        assert results.failure_rate == 0.0
        # Dry run copies actual text → ROUGE-L = 1.0
        assert results.rouge_l_mean == pytest.approx(1.0, abs=1e-3)
        assert results.rating_mae_mean == pytest.approx(0.0, abs=1e-3)
        assert 0.0 <= results.abeg_score_mean <= 1.0

    def test_task_b_dry_run(self, tmp_path):
        records = load_dataset()
        eval_set = build_held_out_set(records, sample_size=5, seed=42)
        config = EvalConfig(
            variant="full",
            sample_size=5,
            seed=42,
            task="b",
            output_dir=tmp_path,
            dry_run=True,
        )
        results = run_task_b_eval(config, eval_set)
        assert results.n == 5
        assert results.failure_rate == 0.0
        # Dry run places target at rank 3 → Hit@10 = 1.0
        assert results.hit_at_10_mean == pytest.approx(1.0)
        assert results.ndcg_at_10_mean > 0.0

    def test_output_files_created(self, tmp_path):
        from tests.eval.harness import save_results, AblationReport, run_task_a_eval, run_task_b_eval

        records = load_dataset()
        eval_set = build_held_out_set(records, sample_size=3, seed=42)
        config = EvalConfig(
            variant="full", sample_size=3, seed=42, task="both",
            output_dir=tmp_path, dry_run=True,
        )
        report = AblationReport(
            timestamp="2026-05-24T00:00:00",
            git_sha="abc1234",
            seed=42,
            sample_size=3,
            task_a={"full": run_task_a_eval(config, eval_set)},
            task_b={"full": run_task_b_eval(config, eval_set)},
        )
        save_results(report, tmp_path)

        json_files = list(tmp_path.glob("*.json"))
        csv_files = list(tmp_path.glob("*.csv"))
        md_files = list(tmp_path.glob("*.md"))
        assert len(json_files) >= 2
        assert len(csv_files) == 1
        assert len(md_files) == 1

        import json
        for jf in json_files:
            data = json.loads(jf.read_text())
            assert "metrics" in data
            assert "meta" in data


# ── Full eval tests (marked eval — not run in default CI) ──────────────────────


@pytest.mark.eval
@pytest.mark.skipif(not DATASET_PATH.exists(), reason="Dataset not present")
class TestFullEval:
    """Run small real eval (needs API keys + ChromaDB). Use:
        pytest -m eval tests/eval/test_harness.py
    """

    def test_task_a_full_small(self, tmp_path):
        records = load_dataset()
        eval_set = build_held_out_set(records, sample_size=10, seed=42)
        config = EvalConfig(
            variant="full", sample_size=10, seed=42,
            task="a", output_dir=tmp_path, dry_run=False,
        )
        results = run_task_a_eval(config, eval_set)
        assert results.n == 10
        assert results.failure_rate <= 0.3
        assert results.rouge_l_mean > 0.0
        assert results.word_count_mean >= 30

    def test_task_b_full_small(self, tmp_path):
        records = load_dataset()
        eval_set = build_held_out_set(records, sample_size=10, seed=42)
        config = EvalConfig(
            variant="full", sample_size=10, seed=42,
            task="b", output_dir=tmp_path, dry_run=False,
        )
        results = run_task_b_eval(config, eval_set)
        assert results.n == 10
        assert results.failure_rate <= 0.3
