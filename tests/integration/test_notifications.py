"""Integration tests: notifications."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_notifications(client: OpenProjectClient) -> None:
    result = await client.get_notifications(page_size=5)
    assert result.get("_type") == "Collection"


async def test_mark_all_read(client: OpenProjectClient) -> None:
    # Should not raise even if there are no notifications
    await client.mark_all_notifications_read()


async def test_mark_single_notification_read(client: OpenProjectClient) -> None:
    result = await client.get_notifications(page_size=1)
    notifications = result.get("_embedded", {}).get("elements", [])
    if not notifications:
        pytest.skip("No notifications to mark read")
    n_id = notifications[0]["id"]
    ok = await client.mark_notification_read(n_id)
    assert ok
