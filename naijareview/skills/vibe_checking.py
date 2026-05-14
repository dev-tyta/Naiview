"""NaijaVibeChecker — compute Vibe Scores, manage active vs passive mode.

Owner: Testimony
See §5 Skill 3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from naijareview.schemas.item import Item
    from naijareview.schemas.user import Fingerprint
    from naijareview.schemas.vibe import VibeScore


class NaijaVibeChecker:
    """Compute Vibe Scores; know about active vs passive mode; decide regen eligibility."""

    def __init__(self, llm_router: object, phrase_library: object) -> None:
        self.llm_router = llm_router
        self.phrase_library = phrase_library
        self.regen_threshold = 0.70  # From config
        self.max_retries = 2

    def score(
        self,
        review_text: str,
        fingerprint: Fingerprint,
        item: Item,
        mode: Literal["passive", "active"],
    ) -> VibeScore:
        """Compute the full Vibe Score for a generated review."""
        # TODO: Implement — lexical + LLM-judged scoring
        raise NotImplementedError

    def should_regenerate(
        self,
        score: VibeScore,
        retry_count: int,
        mode: Literal["passive", "active"],
    ) -> bool:
        """True only if mode=='active' AND score < threshold AND retry_count < max."""
        return (
            mode == "active"
            and score.abeg_score < self.regen_threshold
            and retry_count < self.max_retries
        )

    def regeneration_hint(self, score: VibeScore) -> str:
        """Return a prompt-additive hint based on the weakest sub-score."""
        # TODO: Implement — identify weakest dimension, produce targeted hint
        raise NotImplementedError
