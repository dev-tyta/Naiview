"""AfriSenti phrase loader — curated Nigerian phrases by region × sentiment.

Owner: Shiloh
"""

from __future__ import annotations


class PhraseLibrary:
    """Load and query the AfriSenti-derived Nigerian phrase library."""

    def __init__(self, data_dir: str = "data/phrase_library") -> None:
        self.data_dir = data_dir
        self._phrases: dict = {}
        # TODO: Load JSON phrase files on init

    def get_phrases(
        self,
        region: str,
        sentiment: str,
        category: str | None = None,
    ) -> list[str]:
        """Retrieve phrases matching region, sentiment, and optionally category."""
        # TODO: Implement — fall back to (region, sentiment, *) if exact category sparse
        raise NotImplementedError

    def get_slang_tokens(self) -> set[str]:
        """Return the set of all Nigerian slang/Pidgin tokens for matching."""
        # TODO: Implement
        raise NotImplementedError
