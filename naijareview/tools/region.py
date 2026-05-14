"""Region detection tools: detect_nigerian_region.

See §4.3 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

from langchain_core.tools import tool

from naijareview.schemas.user import RegionProfile, UserHistory


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
    # TODO: Implement — Testimony owns RegionInferenceEngine skill
    raise NotImplementedError("detect_nigerian_region not yet implemented")
