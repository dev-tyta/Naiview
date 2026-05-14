"""RegionInferenceEngine — detect Nigerian region from review history or text.

Owner: Testimony
See §5 Skill 2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from naijareview.schemas.user import RegionProfile, UserHistory


class RegionInferenceEngine:
    """Detect region from history; also from a single sentence (for cold-start)."""

    def from_history(self, history: UserHistory) -> RegionProfile:
        """Infer region from the user's full review history."""
        # TODO: Implement — use regional signal dictionary
        raise NotImplementedError

    def from_text(self, text: str) -> RegionProfile:
        """Infer region from a single piece of text (e.g. cold-start response)."""
        # TODO: Implement — lightweight version of from_history
        raise NotImplementedError

    def boost_with_explicit_signal(
        self, profile: RegionProfile, hint: str
    ) -> RegionProfile:
        """Boost confidence if user explicitly stated location (e.g. 'I'm in Lagos')."""
        # TODO: Implement — check for explicit location mentions
        raise NotImplementedError
