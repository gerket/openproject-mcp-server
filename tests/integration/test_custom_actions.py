"""Integration tests: custom actions.

Requires the "Start work" custom action (ID 1, New → In Progress) created per
docs/integration-test-setup.md Step 4.

NOTE: GET /custom_actions (collection) returns 404 on Community Edition.
Only individual GET and POST execute are available.
"""

import os

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration

CUSTOM_ACTION_ID = int(os.environ.get("OPENPROJECT_CUSTOM_ACTION_ID", "1"))


async def test_get_custom_action(client: OpenProjectClient) -> None:
    result = await client.get_custom_action(CUSTOM_ACTION_ID)
    self_href = result.get("_links", {}).get("self", {}).get("href", "")
    assert str(CUSTOM_ACTION_ID) in self_href, (
        f"Expected ID {CUSTOM_ACTION_ID} in self href, got: {self_href}. "
        "Create the custom action per docs/integration-test-setup.md Step 4."
    )
    assert result.get("name"), "Expected action name"


async def test_execute_custom_action(client: OpenProjectClient, fresh_wp: int) -> None:
    """A fresh WP starts in 'New' status — the 'Start work' action condition."""
    result = await client.execute_custom_action(CUSTOM_ACTION_ID, fresh_wp)
    wp_after = result.get("_embedded", {}).get("workPackage", result)
    status_title = wp_after.get("_links", {}).get("status", {}).get("title", "")
    assert status_title, f"No status title in response: {result}"
    # The 'Start work' action transitions to 'In Progress' (or 'In progress')
    assert (
        "progress" in status_title.lower() or "in" in status_title.lower()
    ), f"Expected 'In Progress' after executing action, got: {status_title!r}"
