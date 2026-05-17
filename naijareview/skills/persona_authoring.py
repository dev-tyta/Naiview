"""PersonaAuthor — translate fingerprint + region + item into a persona prompt block.

Owner: Testimony
See §5 Skill 4 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from naijareview.schemas.item import Item
    from naijareview.schemas.user import Fingerprint, RegionProfile


class PersonaAuthor:
    """Build persona-section text for the generation LLM prompt."""

    def author(
        self,
        fingerprint: "Fingerprint",
        region: "RegionProfile",
        item: "Item",
        intensity: Literal["natural", "amplified"] = "natural",
    ) -> str:
        """Return the persona-section text for the prompt."""
        word_lo, word_hi = fingerprint.verbosity_word_range
        topics = ", ".join(fingerprint.topic_focus) if fingerprint.topic_focus else "various topics"

        if fingerprint.generosity_score > 0.65:
            gen_label = "very generous (tends to rate high)"
        elif fingerprint.generosity_score < 0.40:
            gen_label = "critical (tends to rate low)"
        else:
            gen_label = "balanced"

        block = (
            f"Write as a {fingerprint.emotional_style} reviewer who focuses on {topics}. "
            f"Keep word count between {word_lo}–{word_hi} words. "
            f"This reviewer is {gen_label} with ratings. "
        )

        if region.region != "Unknown" and region.confidence >= 0.4:
            block += f"They are based in {region.region}. "

        if intensity == "amplified":
            block += (
                "AMPLIFY Nigerian register: use more Pidgin, local food references, "
                "and regional expressions. Make it unmistakably Nigerian."
            )
        elif fingerprint.naija_slang_index > 0.05:
            block += (
                f"Naija slang index is {fingerprint.naija_slang_index:.2f} — "
                "sprinkle natural Pidgin expressions where fitting."
            )

        return block
