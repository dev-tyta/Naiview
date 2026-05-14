"""Pydantic schemas — the type system for NaijaReview.

Every tool, node, and skill operates on these contracts.
"""

from naijareview.schemas.auth import (
    TokenPayload,
    TokenResponse,
    UserAccount,
    UserLogin,
    UserRegistration,
    UserSession,
)
from naijareview.schemas.item import Candidate, Item, RankedItem, Recommendation
from naijareview.schemas.output import RecommendationOutput, ReviewOutput
from naijareview.schemas.persona import ColdStartPersona, NigerianPersona
from naijareview.schemas.user import Fingerprint, RegionProfile, Review, UserHistory
from naijareview.schemas.vibe import AbegBreakdown, VibeScore

__all__ = [
    "AbegBreakdown",
    "Candidate",
    "ColdStartPersona",
    "Fingerprint",
    "Item",
    "NigerianPersona",
    "RankedItem",
    "Recommendation",
    "RecommendationOutput",
    "RegionProfile",
    "Review",
    "ReviewOutput",
    "TokenPayload",
    "TokenResponse",
    "UserAccount",
    "UserHistory",
    "UserLogin",
    "UserRegistration",
    "UserSession",
    "VibeScore",
]
