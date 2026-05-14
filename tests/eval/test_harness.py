"""Eval harness tests."""

from __future__ import annotations

import pytest


@pytest.mark.eval
class TestEvalHarness:
    """Tests for the evaluation harness itself."""

    @pytest.mark.skip(reason="Harness not yet implemented")
    def test_harness_config_variants(self):
        """All 5 variants should be constructable."""
        pass
