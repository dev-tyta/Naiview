"""FingerprintBuilder — compute, cache, and manage behavioural fingerprints.

Owner: Testimony
See §5 Skill 1 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from naijareview.schemas.persona import ColdStartPersona
    from naijareview.schemas.user import Fingerprint


def _generosity_from_persona(persona: "ColdStartPersona") -> float:
    vo = getattr(persona, "value_orientation", None)
    if vo == "taste_first":
        return 0.65
    if vo == "value_first":
        return 0.45
    return 0.55


class FingerprintBuilder:
    """Compute fingerprints, manage the cache, handle cold-start vs full users."""

    def __init__(self, cache: object, episodic: object) -> None:
        self.cache = cache
        self.episodic = episodic

    def get_or_build(self, user_id: str) -> "Fingerprint":
        """Return cached fingerprint if fresh, else recompute."""
        from naijareview.tools.fingerprint import build_behavioural_fingerprint

        cached = getattr(self.cache, "get", lambda x: None)(user_id)
        if cached is not None:
            return cached

        history = self.episodic.load_user_history(user_id)
        fp = build_behavioural_fingerprint.invoke({"user_history": history})
        if hasattr(self.cache, "set"):
            self.cache.set(user_id, fp)
        return fp

    def build_from_persona(self, persona: "ColdStartPersona") -> "Fingerprint":
        """Bootstrap a fingerprint from cold-start onboarding answers."""
        from naijareview.schemas.user import Fingerprint

        generosity = _generosity_from_persona(persona)
        topic_focus: list[str] = []
        if persona.food_preference:
            topic_focus = persona.food_preference.split()[:3]

        margin = 0.30
        ci = {
            "generosity_score": (max(0.0, generosity - margin), min(1.0, generosity + margin)),
            "verbosity_score": (0.2, 0.8),
            "consistency_score": (0.2, 0.8),
        }

        return Fingerprint(
            user_id=persona.user_id,
            generosity_score=generosity,
            verbosity_score=0.5,
            verbosity_word_range=(50, 150),
            emotional_intensity=0.4,
            emotional_style="balanced",
            topic_focus=topic_focus,
            consistency_score=0.5,
            recency_weight=0.5,
            naija_slang_index=0.0,
            confidence_intervals=ci,
            computed_at=datetime.now(),
            review_count_at_computation=0,
        )

    def invalidate(self, user_id: str) -> None:
        """Invalidate the cached fingerprint. Called after new review is saved."""
        if hasattr(self.cache, "invalidate"):
            self.cache.invalidate(user_id)
        elif hasattr(self.cache, "delete"):
            self.cache.delete(user_id)
