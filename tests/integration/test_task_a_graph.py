"""Integration tests — Task A graph end-to-end."""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestTaskAGraph:
    """End-to-end tests for the Task A LangGraph."""

    @pytest.mark.skip(reason="Graph not yet implemented")
    def test_full_graph_execution(self):
        """Full graph should produce a review with all metadata."""
        pass

    @pytest.mark.skip(reason="Graph not yet implemented")
    def test_vibe_mode_regeneration_loop(self):
        """Active vibe mode with low score should trigger regeneration."""
        pass
