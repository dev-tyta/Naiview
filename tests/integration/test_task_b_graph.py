"""Integration tests — Task B graph end-to-end."""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestTaskBGraph:
    """End-to-end tests for the Task B LangGraph."""

    @pytest.mark.skip(reason="Graph not yet implemented")
    def test_normal_user_flow(self):
        """User with history should get recommendations."""
        pass

    @pytest.mark.skip(reason="Graph not yet implemented")
    def test_cold_start_flow(self):
        """New user should enter cold-start onboarding."""
        pass
