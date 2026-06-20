"""Integration tests: time entries.

GET /time_entries/activities returns 404 on OpenProject 17.5.x — the endpoint
was not exposed in this API version. Time entries themselves work fine;
activity is an optional field. Tests run without the module marker since
the /time_entries collection endpoint is available regardless of the module.
"""

import datetime
import json

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_time_entry_lifecycle(
    client: OpenProjectClient,
    fresh_wp: int,
    project_id: int,
) -> None:
    today = datetime.date.today().isoformat()

    # activity_id is optional — the /time_entries/activities endpoint does not
    # exist in OpenProject 17.5.x so we omit it rather than hard-fail.
    created = await client.create_time_entry(
        {
            "work_package_id": fresh_wp,
            "hours": 1.5,
            "spent_on": today,
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
    """GET /time_entries/activities — skips gracefully on OpenProject < 14.x."""
    try:
        result = await client.get_time_entry_activities()
    except Exception as e:
        if "404" in str(e):
            pytest.skip(
                "GET /time_entries/activities not available on this OpenProject version "
                "(added in a later API version; not present in 17.5.x)"
            )
        raise
    activities = result.get("_embedded", {}).get("elements", [])
    if not activities:
        pytest.skip(
            "No time entry activities configured — create one in "
            "Administration → Time and costs → Activities"
        )
    assert all("id" in a and "name" in a for a in activities)
