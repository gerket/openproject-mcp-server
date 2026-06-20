"""Integration tests: my_preferences."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_get_my_preferences(client: OpenProjectClient) -> None:
    prefs = await client.get_my_preferences()
    assert isinstance(prefs, dict)
    # timeZone may be empty string if not set, but the key must exist
    assert "timeZone" in prefs


async def test_update_my_preferences_roundtrip(client: OpenProjectClient) -> None:
    """Read current timezone, write it back, verify it sticks."""
    original = await client.get_my_preferences()
    original_tz = original.get("timeZone", "UTC")

    # Write back the same value — a safe no-op that still exercises the endpoint
    updated = await client.update_my_preferences({"timeZone": original_tz})
    assert updated.get("timeZone") == original_tz
