"""Integration tests: notifications.

OpenProject does not generate notifications for self-actions (self-mentions,
self-assignments, or comments on your own WPs). mark_notification_read is
therefore only testable when notifications organically exist from other users
or background activity. The test skips cleanly when the inbox is empty.
"""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_notifications(client: OpenProjectClient) -> None:
    result = await client.get_notifications(page_size=5)
    assert result.get("_type") == "Collection"


async def test_mark_all_read(client: OpenProjectClient) -> None:
    await client.mark_all_notifications_read()


async def test_mark_single_notification_read(client: OpenProjectClient) -> None:
    result = await client.get_notifications(page_size=1)
    notifications = result.get("_embedded", {}).get("elements", [])
    if not notifications:
        pytest.skip(
            "No notifications in inbox. OpenProject suppresses self-notifications, "
            "so this test only runs when another user has triggered a notification "
            "for the test account (e.g. a mention, assignment, or comment on a watched WP)."
        )
    n_id = notifications[0]["id"]
    ok = await client.mark_notification_read(n_id)
    assert ok
