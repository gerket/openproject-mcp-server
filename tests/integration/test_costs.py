"""Integration tests: cost entries and cost types.

GET /cost_types and GET /cost_entries return 404 on OpenProject instances
where the Budgets/Costs module is not active or not available in this API
version. Tests skip gracefully on 404 rather than failing.
"""

import datetime

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_cost_types(client: OpenProjectClient) -> None:
    try:
        result = await client.get_cost_types()
    except Exception as e:
        if "404" in str(e) or "403" in str(e):
            pytest.skip(
                "GET /cost_types not in OpenProject v3 API spec — "
                "cost tracking uses a separate plugin endpoint not part of core v3"
            )
        raise
    cost_types = result.get("_embedded", {}).get("elements", [])
    assert isinstance(cost_types, list)


async def test_cost_entry_lifecycle(
    client: OpenProjectClient, fresh_wp: int, project_id: int
) -> None:
    try:
        types_result = await client.get_cost_types()
    except Exception as e:
        if "404" in str(e) or "403" in str(e):
            pytest.skip("GET /cost_types not in OpenProject v3 API spec")
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
