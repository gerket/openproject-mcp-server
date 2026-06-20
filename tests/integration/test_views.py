"""Integration tests: views."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_views(client: OpenProjectClient) -> None:
    result = await client.get_views()
    views = result.get("_embedded", {}).get("elements", [])
    assert isinstance(views, list)


async def test_get_view(client: OpenProjectClient) -> None:
    result = await client.get_views()
    views = result.get("_embedded", {}).get("elements", [])
    if not views:
        pytest.skip("No views on this instance")
    view_id = views[0]["id"]
    fetched = await client.get_view(view_id)
    assert fetched.get("id") == view_id
    assert fetched.get("name"), "Expected view name"
