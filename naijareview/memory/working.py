"""Working Memory — Context window builder.

See §10.3 of INTERNAL_ARCHITECTURE.md.
Built fresh per LLM call. Not persisted.
"""

from __future__ import annotations


class WorkingMemory:
    """Assembles the prompt context window for a single LLM call.

    Delegates to ContextWindowAssembler skill for the heavy lifting.
    This class handles the lifecycle of a single request's working memory.
    """

    def __init__(self) -> None:
        self.segments: list[str] = []

    def add_segment(self, name: str, content: str) -> None:
        """Add a named segment to the context window."""
        self.segments.append(content)

    def render(self) -> str:
        """Render all segments into a single prompt string."""
        return "\n\n".join(self.segments)

    def clear(self) -> None:
        """Discard all segments (call after LLM response received)."""
        self.segments.clear()
