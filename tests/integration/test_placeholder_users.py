"""Integration tests: placeholder users."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_placeholder_users(client: OpenProjectClient) -> None:
    result = await client.get_placeholder_users()
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_placeholder_user_lifecycle(client: OpenProjectClient) -> None:
    created = await client.create_placeholder_user("MCP Integration Test Placeholder")
    ph_id = created.get("id")
    assert ph_id, f"No id in created placeholder: {created}"
    assert created.get("name") == "MCP Integration Test Placeholder"

    try:
        fetched = await client.get_placeholder_user(ph_id)
        assert fetched.get("id") == ph_id
        assert fetched.get("name") == "MCP Integration Test Placeholder"

        updated = await client.update_placeholder_user(
            ph_id, "MCP Integration Test Placeholder Updated"
        )
        assert updated.get("name") == "MCP Integration Test Placeholder Updated"

        listed = await client.get_placeholder_users()
        ids = [e["id"] for e in listed.get("_embedded", {}).get("elements", [])]
        assert ph_id in ids, f"Created placeholder {ph_id} not in list: {ids}"
    finally:
        ok = await client.delete_placeholder_user(ph_id)
        assert ok
