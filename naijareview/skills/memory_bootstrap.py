"""ColdStartBootstrapper — multi-turn onboarding loop for new users.

Owner: Aaliyah
See §5 Skill 6 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from naijareview.schemas.persona import ColdStartPersona
    from naijareview.schemas.user import Fingerprint


class ColdStartBootstrapper:
    """Run multi-turn onboarding, validate responses, build persona + fingerprint."""

    def __init__(self, llm_router: object, fingerprint_builder: object) -> None:
        self.llm_router = llm_router
        self.fingerprint_builder = fingerprint_builder
        self.required_turns = 3

    def next_turn(
        self, conversation_history: list[dict]
    ) -> tuple[str, ColdStartPersona | None]:
        """Return (agent_utterance, persona_if_complete)."""
        # TODO: Implement — parse turn history, generate next question
        raise NotImplementedError

    def is_complete(self, history: list[dict]) -> bool:
        """Check if all required turns have been completed."""
        # TODO: Implement
        raise NotImplementedError

    def finalise(
        self, history: list[dict]
    ) -> tuple[ColdStartPersona, Fingerprint]:
        """Return the persona and a bootstrapped low-confidence fingerprint."""
        # TODO: Implement
        raise NotImplementedError
