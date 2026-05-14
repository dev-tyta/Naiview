"""Unit tests — fingerprint computation."""

from __future__ import annotations

import pytest


class TestBehaviouralFingerprint:
    """Tests for the build_behavioural_fingerprint tool."""

    @pytest.mark.skip(reason="Not yet implemented")
    def test_fingerprint_from_sufficient_history(self):
        """Users with ≥ 3 reviews should produce a valid fingerprint."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_fingerprint_from_insufficient_history(self):
        """Users with < 3 reviews should produce wide confidence intervals."""
        pass

    @pytest.mark.skip(reason="Not yet implemented")
    def test_fingerprint_caching(self):
        """Second call with same data should return cached result."""
        pass
