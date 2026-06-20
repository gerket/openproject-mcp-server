"""Integration tests: time entries.

Requires the "Time and costs" module enabled in Administration → Modules.
Set OPENPROJECT_MODULE_TIME_COSTS=1 to run these tests.
"""

import datetime
import json

import pytest

from src.client import OpenProjectClient

pytestmark = [pytest.mark.integration, pytest.mark.needs_module_time_costs]


async def test_time_entry_lifecycle(
    client: OpenProjectClient,
    fresh_wp: int,
    project_id: int,
    activity_id: int,
) -> None:
    today = datetime.date.today().isoformat()

    created = await client.create_time_entry(
        {
            "work_package_id": fresh_wp,
            "hours": 1.5,
            "spent_on": today,
            "activity_id": activity_id,
        }
    )
    e_id = created.get("id")
    assert e_id, f"No id in created time entry: {created}"

    try:
        filters = json.dumps(
            [{"project": {"operator": "=", "values": [str(project_id)]}}]
        )
        result = await client.get_time_entries(filters=filters)
        ids = [e["id"] for e in result.get("_embedded", {}).get("elements", [])]
        assert e_id in ids, f"Created time entry {e_id} not in list: {ids}"

        updated = await client.update_time_entry(e_id, {"hours": 2.0})
        assert updated.get("id") == e_id
    finally:
        ok = await client.delete_time_entry(e_id)
        assert ok


async def test_list_time_entry_activities(client: OpenProjectClient) -> None:
    result = await client.get_time_entry_activities()
    activities = result.get("_embedded", {}).get("elements", [])
    assert activities, "Expected at least one time entry activity configured"
    assert all("id" in a and "name" in a for a in activities)
