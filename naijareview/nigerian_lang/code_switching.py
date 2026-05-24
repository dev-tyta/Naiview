"""Code-switching patterns — Yoruba/Igbo/Hausa loanword injection.

Owner: Testimony
Injects regional loanwords at sentence boundaries and as intensifiers,
scaling with the intensity parameter (0.0 = none, 1.0 = heavy injection).
"""

from __future__ import annotations

import random
import re

# Regional loanword dictionaries — injected as interjections / intensifiers
_LOANWORDS: dict[str, dict[str, list[str]]] = {
    "Lagos": {  # Yoruba
        "openers": ["Omo,", "Abeg,", "Abi,"],
        "affirmations": ["Ehen!", "E dey!", "Sha,"],
        "negatives": ["Tufiakwa!", "E no reach!", "Wahala dey o!"],
        "closers": ["Na wa o.", "I no dey lie.", "Abi nah?"],
        "food": ["eba", "ewedu", "gbegiri", "amala", "asun"],
    },
    "Enugu": {  # Igbo
        "openers": ["Nna,", "Biko,", "Chineke,"],
        "affirmations": ["Oya!", "E good o!", "I swear!"],
        "negatives": ["Chai!", "E no good at all!", "God punish!"],
        "closers": ["Na true talk.", "Nna, I no lie.", "Oya now."],
        "food": ["ofe onugbu", "abacha", "akpu", "oha soup", "ugba"],
    },
    "Port Harcourt": {  # Rivers/Ijaw mix
        "openers": ["Sharp sharp,", "Omo,", "Abeg,"],
        "affirmations": ["E dey!", "Na correct!", "I swear!"],
        "negatives": ["E no correct!", "Dem fall hand!", "Na wa!"],
        "closers": ["I no dey lie.", "Na true.", "Sharp!"],
        "food": ["bole", "seafood", "fresh fish", "pepper soup"],
    },
    "Kano": {  # Hausa
        "openers": ["Wallahi,", "Ranka dede,", "Insha Allah,"],
        "affirmations": ["Madalla!", "Na gode!", "E sweet well well!"],
        "negatives": ["Astaghfirullah!", "E no worth am!", "Na wa!"],
        "closers": ["Ranka dede.", "Madalla to dem.", "Insha Allah, I return."],
        "food": ["tuwo shinkafa", "miyan kuka", "suya", "kilishi", "dan wake"],
    },
    "Abuja": {  # Neutral educated Pidgin
        "openers": ["Omo,", "To be honest,", "I tell you,"],
        "affirmations": ["Correct!", "No be small thing!", "E dey!"],
        "negatives": ["E no reach!", "Dem no sabi!", "Na disappointment!"],
        "closers": ["Na so e be.", "I no dey lie.", "Correct correct."],
        "food": ["suya", "shawarma", "kilishi", "local rice"],
    },
    "Unknown": {  # Pan-Nigerian Pidgin — safe default
        "openers": ["Omo,", "I swear,", "No be lie,"],
        "affirmations": ["E dey!", "Correct!", "Top tier!"],
        "negatives": ["E no correct!", "Dem fall hand!", "E disappoint well well!"],
        "closers": ["Na so e be.", "I no dey lie.", "No cap."],
        "food": [],
    },
}


class CodeSwitcher:
    """Handle Yoruba/Igbo/Hausa loanword injection for authentic Nigerian text."""

    def inject_loanwords(
        self,
        text: str,
        region: str,
        intensity: float = 0.3,
        sentiment: str = "positive",
    ) -> str:
        """Inject regional loanwords into text at the specified intensity.

        Args:
            text: Input review text.
            region: Nigerian region ('Lagos', 'Kano', 'Enugu', 'Port Harcourt', 'Abuja', 'Unknown').
            intensity: 0.0 = no injection, 1.0 = inject everywhere eligible.
            sentiment: 'positive', 'negative', or 'neutral'.

        Returns:
            Text enriched with regional loanwords.
        """
        if intensity <= 0.0:
            return text

        vocab = _LOANWORDS.get(region, _LOANWORDS["Unknown"])
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        result: list[str] = []

        for i, sentence in enumerate(sentences):
            s = sentence.strip()
            if not s:
                continue

            # Prepend opener to first sentence with probability = intensity
            if i == 0 and random.random() < intensity:
                opener = random.choice(vocab["openers"])
                s = f"{opener} {s[0].lower()}{s[1:]}"

            # Append affirmation/negative to last sentence
            if i == len(sentences) - 1 and random.random() < intensity:
                closer = random.choice(vocab["closers"])
                if not s.endswith((".", "!", "?")):
                    s += "."
                s += f" {closer}"

            # Inject a mid-sentence affirmation occasionally
            elif random.random() < intensity * 0.3:
                affirm_pool = (
                    vocab["affirmations"] if sentiment != "negative" else vocab["negatives"]
                )
                affirm = random.choice(affirm_pool)
                # Insert before the last word of the sentence
                words = s.split()
                if len(words) > 4:
                    insert_pos = random.randint(len(words) // 2, len(words) - 1)
                    words.insert(insert_pos, affirm)
                    s = " ".join(words)

            result.append(s)

        return " ".join(result)
