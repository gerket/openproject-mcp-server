"""Integration tests: reminders."""

import datetime

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_reminders(client: OpenProjectClient, fresh_wp: int) -> None:
    result = await client.get_reminders(fresh_wp)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_create_reminder(client: OpenProjectClient, fresh_wp: int) -> None:
    remind_at = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    created = await client.create_reminder(
        fresh_wp, remind_at, note="integration test reminder"
    )
    r_id = created.get("id")
    assert r_id, f"No id in created reminder: {created}"

    # Verify it appears in list
    result = await client.get_reminders(fresh_wp)
    ids = [e["id"] for e in result.get("_embedded", {}).get("elements", [])]
    assert r_id in ids, f"Created reminder {r_id} not in list: {ids}"
