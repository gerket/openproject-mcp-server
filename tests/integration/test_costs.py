"""Integration tests: cost entries and cost types.

Requires the "Time and costs" and "Budgets" modules enabled:
Administration → Modules → enable both.
"""

import datetime

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_cost_types(client: OpenProjectClient) -> None:
    try:
        result = await client.get_cost_types()
        cost_types = result.get("_embedded", {}).get("elements", [])
        assert isinstance(cost_types, list)
    except Exception as e:
        if "404" in str(e) or "403" in str(e):
            pytest.skip(
                "Cost types endpoint unavailable — enable 'Time and costs' module in Administration → Modules"
            )
        raise


async def test_cost_entry_lifecycle(
    client: OpenProjectClient, fresh_wp: int, project_id: int
) -> None:
    # Discover a cost type ID first
    try:
        types_result = await client.get_cost_types()
    except Exception as e:
        if "404" in str(e) or "403" in str(e):
            pytest.skip("Cost types unavailable — enable 'Time and costs' module")
        raise

    cost_types = types_result.get("_embedded", {}).get("elements", [])
    if not cost_types:
        pytest.skip(
            "No cost types configured — create one in Administration → Cost types"
        )
    cost_type_id = cost_types[0]["id"]

    today = datetime.date.today().isoformat()
    created = await client.create_cost_entry(
        {
            "project_id": project_id,
            "work_package_id": fresh_wp,
            "cost_type_id": cost_type_id,
            "units": 2.0,
            "spent_on": today,
        }
    )
    e_id = created.get("id")
    assert e_id, f"No id in created cost entry: {created}"

    try:
        listed = await client.get_cost_entries(work_package_id=fresh_wp)
        ids = [e["id"] for e in listed.get("_embedded", {}).get("elements", [])]
        assert e_id in ids, f"Created cost entry {e_id} not in list: {ids}"

        updated = await client.update_cost_entry(e_id, {"units": 3.0})
        assert updated.get("id") == e_id
    finally:
        ok = await client.delete_cost_entry(e_id)
        assert ok
