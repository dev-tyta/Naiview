"""FingerprintBuilder — compute, cache, and manage behavioural fingerprints.

Owner: Testimony
See §5 Skill 1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from naijareview.schemas.persona import ColdStartPersona
    from naijareview.schemas.user import Fingerprint


class FingerprintBuilder:
    """Compute fingerprints, manage the cache, handle cold-start vs full users."""

    def __init__(self, cache: object, episodic: object) -> None:
        self.cache = cache
        self.episodic = episodic

    def get_or_build(self, user_id: str) -> Fingerprint:
        """Return cached fingerprint if fresh, else recompute."""
        # TODO: Implement — check cache freshness, recompute if stale
        raise NotImplementedError

    def build_from_persona(self, persona: ColdStartPersona) -> Fingerprint:
        """Bootstrap a fingerprint from cold-start onboarding answers.

        Maps persona answers to fingerprint dimensions with low confidence
        intervals (because we have no behavioural evidence yet).
        """
        # TODO: Implement — map persona fields to fingerprint dimensions
        raise NotImplementedError

    def invalidate(self, user_id: str) -> None:
        """Invalidate the cached fingerprint. Called after new review is saved."""
        # TODO: Implement — remove from cache
        raise NotImplementedError
