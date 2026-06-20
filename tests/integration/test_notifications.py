"""Integration tests: notifications.

test_mark_single_notification_read requires a second authenticated user
(mcp-test-bot) to trigger a notification for the admin account. Set
OPENPROJECT_BOT_API_KEY in tests/integration/.env after running the setup
script — see scripts/setup_test_project.py click-ops step 1.

Flow: bot creates a WP and assigns it to the admin user → OpenProject
generates a notification of reason "assigned" for the admin → admin reads it.
"""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_notifications(client: OpenProjectClient) -> None:
    result = await client.get_notifications(page_size=5)
    assert result.get("_type") == "Collection"


async def test_mark_all_read(client: OpenProjectClient) -> None:
    await client.mark_all_notifications_read()


async def test_mark_single_notification_read(
    client: OpenProjectClient,
    bot_client: OpenProjectClient | None,
    project_id: int,
    wp_type_id: int,
    current_user_id: int,
) -> None:
    if bot_client is None:
        pytest.skip(
            "OPENPROJECT_BOT_API_KEY not set. Log in as mcp-test-bot, generate an API "
            "token at User menu → Account settings → Access tokens, then add "
            "OPENPROJECT_BOT_API_KEY=<token> to tests/integration/.env."
        )

    # Mark inbox clean first so we're working from a known state
    await client.mark_all_notifications_read()

    # Bot creates a WP assigned to the admin — triggers an "assigned" notification
    wp = await bot_client.create_work_package(
        {
            "project": project_id,
            "subject": "integration-test-notification-trigger",
            "type": wp_type_id,
            "_links": {"assignee": {"href": f"/api/v3/users/{current_user_id}"}},
        }
    )
    wp_id = wp.get("id")
    assert wp_id, f"Bot failed to create WP: {wp}"

    try:
        # Give OpenProject a moment to process the notification
        import asyncio

        await asyncio.sleep(1)

        result = await client.get_notifications(page_size=10)
        notifications = result.get("_embedded", {}).get("elements", [])
        assert notifications, (
            "No notification received after bot assigned WP to admin. "
            "Check that the admin account's notification settings include 'assigned' events "
            "(User menu → My account → Notification settings)."
        )

        n_id = notifications[0]["id"]
        ok = await client.mark_notification_read(n_id)
        assert ok

        # Verify it no longer appears as unread
        await client.mark_all_notifications_read()
    finally:
        try:
            await bot_client.delete_work_package(wp_id)
        except Exception:
            pass
