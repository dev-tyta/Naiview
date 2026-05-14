"""Regional marker dictionaries — signal words for each Nigerian region.

See §4.3 detect_nigerian_region algorithm.
"""

from __future__ import annotations

# Regional signal dictionaries — used by RegionInferenceEngine and detect_nigerian_region tool.
# Organised by region → list of signal words/phrases.

REGION_SIGNALS: dict[str, list[str]] = {
    "Lagos": [
        "VI", "Victoria Island", "Lekki", "Ikeja", "Surulere", "Yaba",
        "traffic", "go-slow", "danfo", "okada", "Ajah", "Ikoyi",
        "Third Mainland", "Oshodi", "Mushin", "Agege",
    ],
    "Abuja": [
        "Wuse", "Maitama", "Garki", "FCT", "Asokoro", "Gwarinpa",
        "Jabi", "Area 1", "Kubwa",
    ],
    "Port Harcourt": [
        "GRA", "Trans Amadi", "PH", "Garden City", "bole", "seafood",
        "Rumuola", "Eleme", "D-Line",
    ],
    "Kano": [
        "Sabon Gari", "suya", "ranka dede", "madalla",
        "Nassarawa", "Fagge", "Bompai",
    ],
    "Enugu": [
        "Independence Layout", "Ogui", "biko", "nna",
        "New Haven", "Achara Layout", "Coal City",
    ],
}
