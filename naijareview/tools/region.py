"""Region detection tools: detect_nigerian_region.

See §4.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import re

from langchain_core.tools import tool

from naijareview.schemas.user import RegionProfile, UserHistory

# Regional signal dictionary (lowercase for case-insensitive matching)
_REGION_SIGNALS: dict[str, list[str]] = {
    "Lagos": [
        "vi", "lekki", "ikeja", "surulere", "yaba", "traffic",
        "go-slow", "danfo", "okada", "island", "mainland", "lagos",
    ],
    "Abuja": [
        "wuse", "maitama", "garki", "fct", "abuja", "asokoro",
        "gwarinpa", "jabi",
    ],
    "Port Harcourt": [
        "gra", "trans amadi", "ph", "garden city", "port harcourt",
        "bole", "seafood", "rumuola",
    ],
    "Kano": [
        "sabon gari", "kano", "hausa", "ranka", "madalla", "kantin kwari",
    ],
    "Enugu": [
        "independence layout", "ogui", "enugu", "biko", "nna", "coal city",
    ],
}


@tool
def detect_nigerian_region(user_history: UserHistory) -> RegionProfile:
    """Infer the user's likely Nigerian region from review-text signals.

    Algorithm:
    1. Concatenate user's last 20 reviews.
    2. Match against regional signal dictionary:
       - Lagos: VI, Lekki, Ikeja, Surulere, Yaba, "traffic", "go-slow", danfo, okada
       - Abuja: Wuse, Maitama, Garki, "FCT"
       - Port Harcourt: GRA, Trans Amadi, "PH", "Garden City", bole, seafood
       - Kano: Sabon Gari, suya terms, Hausa loanwords (ranka dede, madalla)
       - Enugu: Independence Layout, Ogui, Igbo loanwords (biko, nna)
    3. Score each region by signal density.
    4. If max confidence < 0.4, return region="Unknown".

    Args:
        user_history: The user's review history to analyse.

    Returns:
        RegionProfile with region, confidence, and triggering signals.
    """
    # Concatenate last 20 reviews
    recent = user_history.reviews[-20:]
    combined_text = " ".join(r.text for r in recent).lower()

    region_hits: dict[str, list[str]] = {r: [] for r in _REGION_SIGNALS}

    for region, signals in _REGION_SIGNALS.items():
        for signal in signals:
            # Use word-boundary aware search for short signals to avoid false matches
            pattern = re.compile(r"\b" + re.escape(signal.lower()) + r"\b")
            if pattern.search(combined_text):
                region_hits[region].append(signal)

    # Count total unique signals matched across all regions
    total_matched = sum(len(hits) for hits in region_hits.values())

    # Find the region with most hits
    best_region = max(region_hits, key=lambda r: len(region_hits[r]))
    best_count = len(region_hits[best_region])

    # Confidence: matched signals / max(total_signals, 10), clamped [0,1]
    confidence = float(min(1.0, best_count / max(total_matched, 10))) if best_count > 0 else 0.0

    # If no clear winner or below threshold, return Unknown
    if best_count == 0 or confidence < 0.4:
        return RegionProfile(
            user_id=user_history.user_id,
            region="Unknown",
            confidence=0.0,
            signals=[],
        )

    return RegionProfile(
        user_id=user_history.user_id,
        region=best_region,  # type: ignore[arg-type]
        confidence=confidence,
        signals=region_hits[best_region],
    )
