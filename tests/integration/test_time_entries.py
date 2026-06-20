"""Integration tests: time entries."""

import datetime
import json

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


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
    try:
        result = await client.get_time_entry_activities()
    except Exception as e:
        if "404" in str(e) or "403" in str(e):
            pytest.skip(
                "Time entry activities unavailable — enable 'Time and costs' module"
            )
        raise
    activities = result.get("_embedded", {}).get("elements", [])
    assert activities, "Expected at least one time entry activity"
    assert all("id" in a and "name" in a for a in activities)
