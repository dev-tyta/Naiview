"""Unit tests — vibe check scoring."""

from __future__ import annotations

import pytest


class TestVibeCheck:
    """Tests for run_naija_vibe_check tool and NaijaVibeChecker skill."""

    @pytest.mark.skip(reason="Not yet implemented")
    def test_abeg_formula(self):
        """Abeg = 0.4 × authenticity + 0.35 × accuracy + 0.25 × consistency."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_passive_mode_no_regen(self):
        """Passive mode should never trigger regeneration."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_active_mode_below_threshold(self):
        """Active mode with abeg < 0.70 should recommend regeneration."""
        pass
