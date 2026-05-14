"""ContextWindowAssembler — build final prompts with token budgeting.

Owner: Testimony
See §5 Skill 5 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from naijareview.schemas.item import Item
    from naijareview.schemas.user import Fingerprint, RegionProfile


class ContextWindowAssembler:
    """Build the final prompt for the LLM by assembling segments in order."""

    def __init__(self, max_tokens: int = 1000) -> None:
        self.max_tokens = max_tokens

    def assemble_task_a(
        self,
        fingerprint: Fingerprint,
        region: RegionProfile,
        item: Item,
        few_shots: list[str],
        persona_block: str,
        regen_hint: str | None = None,
    ) -> str:
        """Assemble the Task A generation prompt."""
        # TODO: Implement — load jinja template, fill segments, budget tokens
        raise NotImplementedError

    def assemble_task_b_rerank(
        self,
        fingerprint: Fingerprint,
        candidates: list[Item],
        context_query: str,
    ) -> str:
        """Assemble the Task B reranking prompt."""
        # TODO: Implement
        raise NotImplementedError

    def truncate_if_needed(self, segments: list[str], budget: int) -> str:
        """If over budget, drop few-shots first, then truncate fingerprint details."""
        # TODO: Implement — priority-based truncation
        raise NotImplementedError
