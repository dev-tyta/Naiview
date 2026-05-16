"""RegionInferenceEngine — detect Nigerian region from review history or text.

Owner: Testimony
See §5 Skill 2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from datetime import datetime

from naijareview.schemas.user import RegionProfile, Review, UserHistory

_EXPLICIT_SIGNALS: dict[str, list[str]] = {
    "Lagos": ["lagos", "lekki", "ikeja", "vi ", "victoria island", "yaba", "surulere"],
    "Abuja": ["abuja", "fct", "maitama", "wuse", "garki", "asokoro"],
    "Port Harcourt": ["port harcourt", " ph ", "portharcourt", "garden city", "trans amadi"],
    "Kano": ["kano", "sabon gari", "kantin kwari"],
    "Enugu": ["enugu", "independence layout", "ogui", "coal city"],
}


class RegionInferenceEngine:
    """Detect region from history; also from a single sentence (for cold-start)."""

    def from_history(self, history: UserHistory) -> RegionProfile:
        """Infer region from the user's full review history."""
        from naijareview.tools.region import detect_nigerian_region
        return detect_nigerian_region.invoke({"user_history": history})

    def from_text(self, text: str) -> RegionProfile:
        """Infer region from a single piece of text (e.g. cold-start response)."""
        fake_review = Review(
            review_id="tmp",
            user_id="tmp",
            item_id="tmp",
            text=text,
            stars=3.0,
            timestamp=datetime.now(),
            item_category="general",
        )
        fake_history = UserHistory(
            user_id="tmp",
            reviews=[fake_review],
            review_count=1,
        )
        from naijareview.tools.region import detect_nigerian_region
        return detect_nigerian_region.invoke({"user_history": fake_history})

    def boost_with_explicit_signal(
        self, profile: RegionProfile, hint: str
    ) -> RegionProfile:
        """Boost confidence if user explicitly stated location (e.g. 'I'm in Lagos')."""
        hint_lower = hint.lower()
        for region, signals in _EXPLICIT_SIGNALS.items():
            if any(s in hint_lower for s in signals):
                return RegionProfile(
                    user_id=profile.user_id,
                    region=region,  # type: ignore[arg-type]
                    confidence=min(1.0, profile.confidence + 0.4),
                    signals=profile.signals + [f"explicit: {region}"],
                )
        return profile
