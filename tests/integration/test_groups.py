"""Integration tests: groups."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_groups(client: OpenProjectClient) -> None:
    result = await client.get_groups()
    groups = result.get("_embedded", {}).get("elements", result.get("elements", []))
    assert isinstance(groups, list)


async def test_get_group(client: OpenProjectClient) -> None:
    result = await client.get_groups()
    groups = result.get("_embedded", {}).get("elements", result.get("elements", []))
    if not groups:
        pytest.skip("No groups configured on this instance")
    g_id = groups[0]["id"]
    fetched = await client.get_group(g_id)
    assert fetched["id"] == g_id
