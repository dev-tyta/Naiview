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
        fingerprint: Fingerprint,
        region: RegionProfile,
        item: Item,
        intensity: Literal["natural", "amplified"] = "natural",
    ) -> str:
        """Return the persona-section text for the prompt.

        intensity='amplified' is used when Naija Vibe Mode is active and
        we're retrying after a low score — it dials up the Nigerian register
        instructions and selects stronger few-shot examples.
        """
        # TODO: Implement — build persona block from fingerprint dims
        raise NotImplementedError
