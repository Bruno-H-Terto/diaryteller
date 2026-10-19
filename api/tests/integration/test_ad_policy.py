"""Ad policy follows the effective plan and the feature flags."""

from __future__ import annotations

import pytest
from helpers import auth_headers, register_and_login

pytestmark = pytest.mark.integration


async def test_free_tier_policy_respects_flags(client, database) -> None:
    tokens = await register_and_login(
        client, database, "ads@example.com", "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    )
    headers = auth_headers(tokens)
    disabled = await client.get("/v1/monetization/ad-policy", headers=headers)
    assert disabled.status_code == 200, disabled.text
    assert disabled.json() == {
        "tier": "free",
        "enabled": False,
        "placements": [],
        "rewarded_enabled": False,
        "policy_version": "local-fixture-1",
    }
    from identity.app import app

    settings = app.state.container.settings
    original = (settings.ads_enabled, settings.rewarded_ads_enabled)
    settings.ads_enabled = True
    settings.rewarded_ads_enabled = True
    try:
        enabled = await client.get("/v1/monetization/ad-policy", headers=headers)
        body = enabled.json()
        assert body["enabled"] is True
        assert body["rewarded_enabled"] is True
        assert body["placements"] == ["home_banner", "post_save_interstitial"]
    finally:
        settings.ads_enabled, settings.rewarded_ads_enabled = original


async def test_ad_policy_requires_authentication(client, database) -> None:
    response = await client.get("/v1/monetization/ad-policy")
    assert response.status_code == 401
