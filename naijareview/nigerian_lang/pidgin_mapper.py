"""English → Nigerian Pidgin phrase/word mapping.

Owner: Shiloh
Applies deterministic substitutions on top of LLM-generated text to
increase authentic Pidgin density without rewriting the entire review.
"""

from __future__ import annotations

import re
import random

# Phrase-level substitutions (applied first — longest match wins)
_PHRASE_MAP: list[tuple[str, list[str]]] = [
    # Affirmations / agreement
    (r"\bvery good\b", ["too good", "sweet well well", "sharp sharp"]),
    (r"\breally good\b", ["dey very good", "too much", "correct"]),
    (r"\bso good\b", ["too good sef", "sweet die"]),
    (r"\bexcellent\b", ["top tier", "correct correct", "e too much"]),
    (r"\bamazing\b", ["too much", "dey burst brain", "e don sweet me"]),
    (r"\boutstanding\b", ["correct correct", "no be joke"]),
    (r"\bwonderful\b", ["sweet well well", "e don sweet me die"]),
    (r"\bfantastic\b", ["top tier", "e burst"]),
    (r"\bincredible\b", ["no be small thing", "e pass understanding"]),
    (r"\bdelicious\b", ["sweet well well", "e dey burst brain"]),
    (r"\btasty\b", ["sweet die", "e dey enter body"]),
    (r"\bfresh\b", ["fresh die", "sharp sharp fresh"]),
    # Negatives
    (r"\bterrible\b", ["bad bad", "e no good at all"]),
    (r"\bawful\b", ["too bad", "e no sabi anything"]),
    (r"\bdisappointing\b", ["e disappoint me well well", "e no meet expectation"]),
    (r"\bnot good\b", ["e no good", "dem no sabi"]),
    (r"\bpoor\b", ["e no reach", "dem fall hand"]),
    # Action phrases
    (r"\bI will definitely\b", ["I go surely"]),
    (r"\bI will\b", ["I go"]),
    (r"\bI would\b", ["I for"]),
    (r"\bI recommend\b", ["I dey recommend"]),
    (r"\byou should\b", ["make you"]),
    (r"\bcome back\b", ["come back again"]),
    (r"\bhighly recommend\b", ["recommend am well well"]),
    # Filler / emphasis
    (r"\bI must say\b", ["I tell you"]),
    (r"\bI have to say\b", ["honestly"]),
    (r"\bto be honest\b", ["no be lie"]),
    (r"\bhonestly\b", ["no be lie", "I swear"]),
    (r"\bactually\b", ["sha", "sef"]),
    (r"\bbasically\b", ["na so e be"]),
    (r"\boverall\b", ["all in all", "on top of everything"]),
    # Value
    (r"\bgood value\b", ["e get value for money", "correct value"]),
    (r"\bworth it\b", ["e worth am", "e get am for am"]),
    (r"\breasonable price\b", ["price dey okay", "price e correct"]),
    (r"\baffordable\b", ["e no too cost", "price dey manageable"]),
    # Experience
    (r"\bI enjoyed\b", ["e sweet me", "I enjoy am"]),
    (r"\bI loved\b", ["e burst my belle", "I love am well well"]),
    (r"\bI liked\b", ["I like am", "e enter my eye"]),
    (r"\bgreat experience\b", ["correct experience", "e sweet well well"]),
    (r"\bgreat\b", ["correct", "e dey burst"]),
]

# Word-level substitutions (applied after phrase substitutions)
_WORD_MAP: dict[str, list[str]] = {
    "the": ["the"],  # keep — don't drop "the" in Pidgin
    "very": ["well well", "too", "very"],
    "really": ["no be lie,", "I swear,", "really"],
    "nice": ["nice", "sweet", "correct"],
    "good": ["good", "correct", "sweet"],
    "best": ["best", "top tier", "correct pass"],
    "food": ["food", "chop"],
    "eat": ["chop", "eat"],
    "ate": ["chop", "eat"],
    "come": ["come", "enter"],
    "go": ["go", "enter"],
    "service": ["service", "them sabi their work"],
    "staff": ["staff", "people wey dey serve"],
    "friendly": ["friendly", "dem too kind", "dem dey carry go"],
    "definitely": ["surely", "no doubt", "definitely"],
    "again": ["again", "come back again"],
}

# Sentence-ending Pidgin exclamations (appended occasionally)
_NAIJA_ENDINGS = [
    "No cap!",
    "I swear!",
    "No be small thing.",
    "Na so e be o!",
    "E don make sense.",
    "Madalla!",
    "I no dey lie.",
    "E don sweet me die!",
]


class PidginMapper:
    """Map standard English phrases to Nigerian Pidgin equivalents.

    Applies phrase-level substitutions then word-level substitutions.
    Intensity controls what fraction of eligible substitutions are applied.
    """

    def __init__(self) -> None:
        self._compiled = [
            (re.compile(pattern, re.IGNORECASE), replacements)
            for pattern, replacements in _PHRASE_MAP
        ]

    def to_pidgin(self, text: str, intensity: float = 0.5) -> str:
        """Convert English text to Pidgin with controllable intensity.

        Args:
            text: Input English or lightly-Pidginised text.
            intensity: 0.0 = no changes, 1.0 = apply all substitutions.

        Returns:
            Pidgin-flavoured text.
        """
        if intensity <= 0.0:
            return text

        result = text

        # Phrase substitutions
        for pattern, replacements in self._compiled:
            if random.random() > intensity:
                continue
            result = pattern.sub(
                lambda m, r=replacements: random.choice(r),
                result,
                count=1,
            )

        # Occasionally append a Naija sentence ending
        if intensity >= 0.6 and random.random() < intensity * 0.4:
            if not result.rstrip().endswith(tuple("!.?")):
                result = result.rstrip() + "."
            result += " " + random.choice(_NAIJA_ENDINGS)

        return result

    def naija_density(self, text: str) -> float:
        """Rough estimate of Pidgin density — fraction of phrase patterns matched."""
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return 0.0
        pidgin_markers = {
            "omo", "sha", "sef", "na", "dey", "abeg", "wahala", "chop", "sabi",
            "nna", "biko", "ranka", "madalla", "correct", "burst", "wey", "dem",
        }
        matches = sum(1 for t in tokens if t in pidgin_markers)
        return matches / len(tokens)
