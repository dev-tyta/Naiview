"""AfriSenti phrase loader — curated Nigerian phrases by region × sentiment × category.

Owner: Shiloh
Data: data/phrase_library/indexed_library.json
      data/phrase_library/examples_by_sentiment.json
      data/phrase_library/regional_markers.json
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

_DATA_DIR = Path("data/phrase_library")
_INTENSITY = Literal["heavy", "amplified", "natural"]


class PhraseLibrary:
    """Load and query the AfriSenti-derived Nigerian phrase library."""

    def __init__(self, data_dir: str | Path = _DATA_DIR) -> None:
        self.data_dir = Path(data_dir)
        self._indexed: dict = {}          # region → sentiment → category → intensity → [str]
        self._by_sentiment: dict = {}     # sentiment → [phrases]
        self._regional_markers: dict = {} # region → [markers]
        self._slang_tokens: set[str] = set()
        self._load()

    def _load(self) -> None:
        try:
            indexed_path = self.data_dir / "indexed_library.json"
            if indexed_path.exists():
                self._indexed = json.loads(indexed_path.read_text())

            sent_path = self.data_dir / "examples_by_sentiment.json"
            if sent_path.exists():
                self._by_sentiment = json.loads(sent_path.read_text())

            markers_path = self.data_dir / "regional_markers.json"
            if markers_path.exists():
                self._regional_markers = json.loads(markers_path.read_text())

            # Build slang token set from all indexed examples
            corpus_path = self.data_dir / "token_corpus.txt"
            if corpus_path.exists():
                self._slang_tokens = {
                    line.split("\t")[0].strip().lower()
                    for line in corpus_path.read_text().splitlines()
                    if line.strip()
                }

            logger.info(
                "PhraseLibrary loaded: %d regions, %d slang tokens",
                len(self._indexed),
                len(self._slang_tokens),
            )
        except Exception as exc:
            logger.warning("PhraseLibrary load failed: %s", exc)

    def get_phrases(
        self,
        region: str,
        sentiment: str,
        category: str | None = None,
        intensity: _INTENSITY = "natural",
        k: int = 3,
    ) -> list[str]:
        """Retrieve k phrases matching region × sentiment × category × intensity.

        Falls back: region+sentiment+category → region+sentiment → sentiment only.
        """
        results: list[str] = []

        # 1. Try region × sentiment × category
        if category and region in self._indexed:
            r_data = self._indexed[region]
            s_data = r_data.get(sentiment, r_data.get("positive", {}))
            for cat_key, intensities in s_data.items():
                if category.lower() in cat_key.lower() or cat_key.lower() in category.lower():
                    phrases = intensities.get(intensity, intensities.get("natural", []))
                    results.extend(phrases)
                    if len(results) >= k:
                        break

        # 2. Fall back to all categories in this region × sentiment
        if len(results) < k and region in self._indexed:
            r_data = self._indexed[region]
            s_data = r_data.get(sentiment, r_data.get("positive", {}))
            for intensities in s_data.values():
                phrases = intensities.get(intensity, intensities.get("natural", []))
                results.extend(phrases)
                if len(results) >= k * 2:
                    break

        # 3. Fall back to sentiment-only bucket
        if len(results) < k:
            results.extend(self._by_sentiment.get(sentiment, []))

        random.shuffle(results)
        return results[:k]

    def get_regional_markers(self, region: str) -> list[str]:
        """Return the list of regional marker words for this region."""
        return self._regional_markers.get(region, [])

    def get_slang_tokens(self) -> set[str]:
        """Return the full set of Nigerian slang/Pidgin tokens."""
        return self._slang_tokens

    def naija_density(self, text: str) -> float:
        """Fraction of tokens in text that match Nigerian slang corpus."""
        if not self._slang_tokens:
            return 0.0
        import re
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return 0.0
        matches = sum(1 for t in tokens if t in self._slang_tokens)
        return matches / len(tokens)
