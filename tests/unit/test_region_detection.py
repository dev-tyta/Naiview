"""Unit tests — region detection."""

from __future__ import annotations

import pytest


class TestRegionDetection:
    """Tests for detect_nigerian_region tool."""

    @pytest.mark.skip(reason="Not yet implemented")
    def test_lagos_signals(self):
        """Reviews mentioning Lekki, danfo, etc. should detect Lagos."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_unknown_region(self):
        """Reviews without regional signals should return Unknown."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_confidence_threshold(self):
        """Max confidence < 0.4 should return Unknown."""
        pass
