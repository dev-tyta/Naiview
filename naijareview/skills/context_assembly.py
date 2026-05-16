"""ContextWindowAssembler — build final prompts with token budgeting.

Owner: Testimony
See §5 Skill 5 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from naijareview.schemas.item import Item
    from naijareview.schemas.user import Fingerprint, RegionProfile

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"


def _render_jinja(template_name: str, **ctx: object) -> str:
    """Render a Jinja2 template from the prompts directory."""
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)), autoescape=False)
    tpl = env.get_template(template_name)
    return tpl.render(**ctx)


def _approx_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 chars."""
    return len(text) // 4


class ContextWindowAssembler:
    """Build the final prompt for the LLM by assembling segments in order."""

    def __init__(self, max_tokens: int = 1000) -> None:
        self.max_tokens = max_tokens

    def assemble_task_a(
        self,
        fingerprint: "Fingerprint",
        region: "RegionProfile",
        item: "Item",
        few_shots: list[str],
        persona_block: str,
        naija_vibe_mode: bool = False,
        item_analysis: dict | None = None,
        regen_hint: str | None = None,
    ) -> str:
        """Assemble the Task A generation prompt via the Jinja template."""
        from naijareview.nigerian_lang.region_signals import REGION_SIGNALS
        regional_markers = REGION_SIGNALS.get(region.region, [])

        inferred_sentiment = (item_analysis or {}).get("inferred_sentiment", "neutral")
        predicted_rating_range = (item_analysis or {}).get("predicted_rating_range", "3-4 stars")

        # Budget few_shots: drop from the end if over token limit
        budgeted_shots = self._budget_few_shots(few_shots)

        try:
            prompt = _render_jinja(
                "task_a_generate.jinja",
                naija_vibe_mode=naija_vibe_mode,
                generosity=round(fingerprint.generosity_score, 2),
                verbosity_word_range=fingerprint.verbosity_word_range,
                emotional_style=fingerprint.emotional_style,
                topic_focus=fingerprint.topic_focus,
                slang_index=round(fingerprint.naija_slang_index, 3),
                consistency_score=round(fingerprint.consistency_score, 2),
                region=region.region,
                region_confidence=round(region.confidence, 2),
                regional_markers=regional_markers,
                item=item,
                inferred_sentiment=inferred_sentiment,
                predicted_rating_range=predicted_rating_range,
                few_shots=budgeted_shots,
                persona_block=persona_block,
                regen_hint=regen_hint,
            )
        except Exception:
            # Fallback: minimal prompt
            prompt = (
                f"Write a {fingerprint.emotional_style} review for '{item.name}' "
                f"({item.category}). {persona_block} "
                f"Return JSON: {{\"review\": \"...\", \"rating\": 4.0}}"
            )

        return prompt

    def assemble_task_b_rerank(
        self,
        fingerprint: "Fingerprint",
        candidates: list["Item"],
        context_query: str,
    ) -> str:
        """Assemble the Task B reranking prompt."""
        lines = "\n".join(
            f"{i+1}. {c.name} ({c.category}, {c.avg_rating:.1f}★)"
            for i, c in enumerate(candidates)
        )
        topics = ", ".join(fingerprint.topic_focus) or "general"
        return (
            f"Rerank these items for a user interested in {topics}, "
            f"who is {fingerprint.emotional_style} and rates {fingerprint.generosity_score:.1f}/1.0.\n"
            f"Request: \"{context_query}\"\n\n{lines}\n\n"
            f"Return JSON: {{\"rankings\": [{{\"item_index\": 1, \"rank\": 1, "
            f"\"alignment_score\": 0.9, \"reasoning_snippet\": \"...\"}}]}}"
        )

    def truncate_if_needed(self, segments: list[str], budget: int) -> str:
        """Drop few-shots first, then truncate remaining if still over budget."""
        # segments: [system, fingerprint, item, few_shots..., persona, constraints]
        # Drop from the middle (few-shots) first
        result = list(segments)
        while _approx_tokens("\n\n".join(result)) > budget and len(result) > 2:
            # Remove from position 3 onward (few-shots zone) if possible
            mid = len(result) // 2
            result.pop(mid)
        return "\n\n".join(result)

    def _budget_few_shots(self, few_shots: list[str], max_tokens: int = 300) -> list[str]:
        """Return as many few-shots as fit within the token budget."""
        result: list[str] = []
        used = 0
        for shot in few_shots:
            tokens = _approx_tokens(shot)
            if used + tokens > max_tokens:
                break
            result.append(shot)
            used += tokens
        return result
