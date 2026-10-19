"""Tier-based advertising policy delivered to the Android client.

The backend decides placements from the effective plan. It never receives or
forwards diary content, and rewarded ads remain disabled until a provider and
its verified callback are chosen.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AdPlacement(StrEnum):
    """Non-critical placements allowed by the MVP policy."""

    HOME_BANNER = "home_banner"
    POST_SAVE_INTERSTITIAL = "post_save_interstitial"


class AdPolicy(BaseModel):
    """Policy for one account tier."""

    model_config = ConfigDict(extra="forbid")

    tier: str
    enabled: bool
    placements: list[AdPlacement] = Field(default_factory=list)
    rewarded_enabled: bool = False
    policy_version: str
