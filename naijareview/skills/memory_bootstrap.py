"""ColdStartBootstrapper — multi-turn onboarding loop for new users.

Owner: Aaliyah
See §5 Skill 6 of INTERNAL_ARCHITECTURE.md.

Runs a 3-turn conversational interview to build a ``ColdStartPersona``
and a low-confidence bootstrapped ``Fingerprint``.

Turn sequence:
  Turn 1: Ask food preference → parse → store ``food_preference``
  Turn 2: Ask value orientation → parse → store ``value_orientation``
  Turn 3: Ask atmosphere + budget → parse → store both
  After turn 3 → return completed ``ColdStartPersona``
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from naijareview.llm.router import LLMRouter
from naijareview.schemas.persona import ColdStartPersona

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "llm" / "prompts"
_TURN_TEMPLATES = {
    1: "cold_start_turn_1.jinja",
    2: "cold_start_turn_2.jinja",
    3: "cold_start_turn_3.jinja",
}


class ColdStartBootstrapper:
    """Run multi-turn onboarding, validate responses, build persona."""

    def __init__(
        self,
        llm_router: LLMRouter,
        naija_vibe_mode: bool = False,
    ) -> None:
        self.llm_router = llm_router
        self.naija_vibe_mode = naija_vibe_mode
        self.required_turns = 3
        self._env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)))

    # ── Public API ───────────────────────────────────────────────────────

    def next_turn(
        self,
        conversation_history: list[dict[str, str]],
    ) -> tuple[str, ColdStartPersona | None]:
        """Process the latest user response and emit the next agent utterance.

        Args:
            conversation_history: List of ``{"role": "user"|"assistant", "content": ...}``
                                  dicts representing the conversation so far.
                                  The last message should be the user's latest response.

        Returns:
            Tuple of (agent_utterance, completed_persona_or_None).
            If all 3 turns are complete, ``agent_utterance`` is the warm wrap-up
            message and ``persona`` is the fully populated ``ColdStartPersona``.
            Otherwise ``persona`` is ``None``.
        """
        user_turns = self._count_user_turns(conversation_history)

        # Determine which turn we're processing (1-indexed)
        current_turn = user_turns + 1  # 1st user message → turn 1, etc.

        if current_turn > self.required_turns:
            # All turns already complete — just return final persona
            persona = self._build_persona(conversation_history)
            return "You're all set! Let me find some great recommendations for you...", persona

        # Render the prompt for this turn
        prompt = self._render_turn(current_turn, conversation_history)

        # Call the LLM
        try:
            raw = self.llm_router.call_with_retry(
                "utility",
                prompt,
                max_tokens=300,
                temperature=0.5,
            )
        except Exception as exc:
            logger.error("Cold-start LLM call failed on turn %d: %s", current_turn, exc)
            return self._fallback_utterance(current_turn), None

        # Parse the JSON response
        try:
            parsed = self._parse_llm_response(raw)
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Cold-start parse failed on turn %d: %s", current_turn, exc)
            return self._fallback_utterance(current_turn), None

        agent_utterance = parsed.get("agent_utterance", self._fallback_utterance(current_turn))

        # Check if we're done after this turn
        if current_turn >= self.required_turns:
            # Actually, persona is built from the full history, not just this turn's LLM output
            persona = self._build_persona(conversation_history)
            return agent_utterance, persona

        return agent_utterance, None

    def is_complete(self, history: list[dict[str, str]]) -> bool:
        """Check if all required turns have been completed."""
        return self._count_user_turns(history) >= self.required_turns

    def finalise(self, history: list[dict[str, str]]) -> ColdStartPersona:
        """Build and return the final persona from a completed conversation."""
        return self._build_persona(history)

    # ── Internals ────────────────────────────────────────────────────────

    def _count_user_turns(self, history: list[dict[str, str]]) -> int:
        return sum(1 for m in history if m.get("role") == "user")

    def _render_turn(
        self,
        turn: int,
        history: list[dict[str, str]],
    ) -> str:
        """Render the Jinja prompt template for the given turn."""
        template_name = _TURN_TEMPLATES.get(turn)
        if template_name is None:
            msg = f"No template for turn {turn}"
            raise ValueError(msg)

        template = self._env.get_template(template_name)

        # Build template variables from history
        last_user_msg = ""
        food_pref = ""
        value_orient = ""

        # Extract what we've already parsed by re-running previous turns' logic
        # (Simulates the accumulated context — real persistence would be better,
        #  but for a 3-turn hackathon flow this is acceptable)
        for i in range(1, turn):
            # Re-parse previous turns from the history to build context
            pass

        # Simpler: just search for the last user message
        user_messages = [m for m in history if m.get("role") == "user"]
        if user_messages:
            last_user_msg = user_messages[-1].get("content", "")

        # For turns 2 and 3, we need the previous parsing results.
        # We re-parse the earlier turns from the LLM responses stored in history.
        assistant_msgs = [m for m in history if m.get("role") == "assistant"]

        if turn >= 2 and len(assistant_msgs) >= 1:
            # Try to extract food_preference from turn 1's LLM response
            # The LLM stored its parsed output as JSON in the assistant message
            try:
                turn1_response = json.loads(assistant_msgs[0].get("content", "{}"))
                parsed = turn1_response.get("parsed", {})
                food_pref = parsed.get("food_preference", "") or ""
            except (json.JSONDecodeError, IndexError):
                pass

        if turn >= 3 and len(assistant_msgs) >= 2:
            try:
                turn2_response = json.loads(assistant_msgs[1].get("content", "{}"))
                parsed = turn2_response.get("parsed", {})
                value_orient = parsed.get("value_orientation", "balanced")
            except (json.JSONDecodeError, IndexError):
                value_orient = "balanced"

        return template.render(
            user_message=last_user_msg,
            food_preference=food_pref,
            value_orientation=value_orient,
            naija_vibe_mode=self.naija_vibe_mode,
        )

    def _parse_llm_response(self, raw: str) -> dict[str, Any]:
        """Extract the JSON object from the LLM's response."""
        # Try to parse the entire response as JSON first
        raw = raw.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            lines = raw.splitlines()
            # Find the first and last ```
            start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    start = i + 1
                    break
            end = len(lines)
            for i in range(len(lines) - 1, start - 1, -1):
                if lines[i].strip().startswith("```"):
                    end = i
                    break
            raw = "\n".join(lines[start:end])

        return json.loads(raw.strip())

    def _build_persona(self, history: list[dict[str, str]]) -> ColdStartPersona:
        """Build a ColdStartPersona from the conversation history by re-parsing
        the structured data the LLM left for us in its assistant responses."""
        assistant_msgs = [m for m in history if m.get("role") == "assistant"]

        food_preference: str | None = None
        value_orientation: str | None = None
        atmosphere_preference: str | None = None
        budget_range: str | None = None

        for msg in assistant_msgs:
            try:
                data = json.loads(msg.get("content", "{}"))
                parsed = data.get("parsed", {})

                if parsed.get("food_preference"):
                    food_preference = parsed["food_preference"]
                if parsed.get("value_orientation"):
                    value_orientation = parsed["value_orientation"]
                if parsed.get("atmosphere_preference"):
                    atmosphere_preference = parsed["atmosphere_preference"]
                if parsed.get("budget_range"):
                    budget_range = parsed["budget_range"]
            except (json.JSONDecodeError, TypeError):
                continue

        # Defaults for anything not yet provided
        return ColdStartPersona(
            user_id="cold_start",
            food_preference=food_preference,
            value_orientation=value_orientation or "balanced",  # type: ignore[arg-type]
            atmosphere_preference=atmosphere_preference or "either",  # type: ignore[arg-type]
            budget_range=budget_range or "mid",  # type: ignore[arg-type]
            frequency_of_dining_out="occasional",
            turns_completed=min(len(assistant_msgs), self.required_turns),
        )

    def _fallback_utterance(self, turn: int) -> str:
        """Return a safe fallback utterance if the LLM call fails."""
        fallbacks = {
            1: "What kind of food do you normally enjoy? (e.g. Nigerian, continental, or a mix?)",
            2: "Do you care more about taste, value for money, or a balance of both?",
            3: "Last one! Do you prefer lively spots or quieter places? And budget-wise — affordable, mid-range, or premium?",
        }
        return fallbacks.get(turn, "Tell me a bit more about what you're looking for!")
