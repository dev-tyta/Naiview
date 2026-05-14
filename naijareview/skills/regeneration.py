"""RegenerationStrategist — plan how to fix a low-scoring review.

Owner: Testimony
See §5 Skill 7 of INTERNAL_ARCHITECTURE.md.

Called by plan_regeneration node when:
  naija_vibe_mode=True AND abeg_score < 0.70 AND retry_count < 2

The strategist inspects which sub-score was weakest and returns a
RegenerationPlan that the next author_persona + assemble_prompt pass consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from naijareview.schemas.user import RegionProfile
from naijareview.schemas.vibe import VibeScore


@dataclass
class RegenerationPlan:
    """Instructions for the next generation attempt."""

    target_dimension: str
    prompt_addition: str
    swap_few_shots: bool = False
    new_few_shots: list[str] = field(default_factory=list)
    bump_intensity: bool = False


class RegenerationStrategist:
    """Decide *how* to regenerate when Vibe Mode is on and a score is low.

    Different weak sub-scores need different fixes:
    - cultural_authenticity low  → swap few-shots for heavier register, bump intensity
    - cultural_accuracy low      → inject region-specific guidance, correct bad terms
    - persona_consistency low    → tighten verbosity and emotional-style constraints
    """

    # Minimum gap to call a dimension "clearly weakest"
    _DOMINANCE_MARGIN: float = 0.05

    def plan(
        self,
        vibe_score: VibeScore,
        current_few_shots: list[str],
        region: RegionProfile,
    ) -> RegenerationPlan:
        """Return a RegenerationPlan targeting the weakest vibe dimension.

        See §5 Skill 7 of INTERNAL_ARCHITECTURE.md.

        Args:
            vibe_score: The VibeScore from the previous attempt.
            current_few_shots: Few-shot examples used in the previous attempt.
            region: The inferred region profile.

        Returns:
            RegenerationPlan with targeted instructions.
        """
        dim, score = self._weakest_dimension(vibe_score)

        if dim == "cultural_authenticity":
            return self._plan_authenticity(vibe_score, region)
        if dim == "cultural_accuracy":
            return self._plan_accuracy(vibe_score, region)
        return self._plan_persona_consistency(vibe_score)

    # ── Private planners ─────────────────────────────────────────────────────

    def _weakest_dimension(self, score: VibeScore) -> tuple[str, float]:
        dims = {
            "cultural_authenticity": score.cultural_authenticity,
            "cultural_accuracy": score.cultural_accuracy,
            "persona_consistency": score.persona_consistency,
        }
        return min(dims.items(), key=lambda kv: kv[1])

    def _plan_authenticity(self, score: VibeScore, region: RegionProfile) -> RegenerationPlan:
        slang_note = (
            f"The review sounds too formal/generic. "
            f"Use more natural Nigerian phrasing appropriate to the user's Slang Index. "
            f"Avoid AI filler phrases like 'I highly recommend' or 'great experience'. "
        )
        if region.region != "Unknown":
            slang_note += (
                f"Incorporate at least one natural {region.region}-specific expression "
                f"or cultural reference if it fits the context."
            )

        return RegenerationPlan(
            target_dimension="cultural_authenticity",
            prompt_addition=slang_note,
            swap_few_shots=True,
            bump_intensity=True,
        )

    def _plan_accuracy(self, score: VibeScore, region: RegionProfile) -> RegenerationPlan:
        accuracy_note = (
            "Cultural references in the previous attempt were incorrect or implausible. "
            "Use only food names, place references, and slang that are accurate for "
        )
        if region.region != "Unknown":
            accuracy_note += (
                f"the {region.region} region specifically. "
                f"If unsure of a specific term, use a general Nigerian expression instead."
            )
        else:
            accuracy_note += (
                "a general Nigerian context — avoid any region-specific claims "
                "when the user's region is unknown."
            )

        return RegenerationPlan(
            target_dimension="cultural_accuracy",
            prompt_addition=accuracy_note,
            swap_few_shots=False,
            bump_intensity=False,
        )

    def _plan_persona_consistency(self, score: VibeScore) -> RegenerationPlan:
        consistency_note = (
            "The review did not match the user's documented style. "
            "Pay strict attention to: "
            "(1) word count — stay within the verbosity range specified, "
            "(2) emotional style — match the stated label exactly, "
            "(3) topic focus — mention the user's habitual topics, "
            "(4) generosity — the rating must reflect the tone of the text."
        )
        return RegenerationPlan(
            target_dimension="persona_consistency",
            prompt_addition=consistency_note,
            swap_few_shots=False,
            bump_intensity=False,
        )
