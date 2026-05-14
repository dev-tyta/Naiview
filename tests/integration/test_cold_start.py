"""Integration tests — cold-start onboarding."""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestColdStart:
    """Tests for the cold-start multi-turn onboarding flow."""

    @pytest.mark.skip(reason="Not yet implemented")
    def test_three_turn_completion(self):
        """After 3 turns, a ColdStartPersona should be fully populated."""
        pass
