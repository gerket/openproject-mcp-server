"""Integration tests: watchers and activity editing."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_watchers(client: OpenProjectClient, fresh_wp: int) -> None:
    result = await client.get_watchers(fresh_wp)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_available_watchers(client: OpenProjectClient, fresh_wp: int) -> None:
    result = await client.get_available_watchers(fresh_wp)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_add_remove_watcher(
    client: OpenProjectClient, fresh_wp: int, current_user_id: int
) -> None:
    await client.add_watcher(fresh_wp, current_user_id)
    watchers = client.get_watchers(fresh_wp)
    result = await watchers
    ids = [int(w.get("id", 0)) for w in result.get("_embedded", {}).get("elements", [])]
    assert (
        current_user_id in ids
    ), f"User {current_user_id} not in watchers after add: {ids}"

    await client.remove_watcher(fresh_wp, current_user_id)
    result_after = await client.get_watchers(fresh_wp)
    ids_after = [
        int(w.get("id", 0))
        for w in result_after.get("_embedded", {}).get("elements", [])
    ]
    assert (
        current_user_id not in ids_after
    ), f"User {current_user_id} still in watchers after remove: {ids_after}"


async def test_available_assignees(client: OpenProjectClient, fresh_wp: int) -> None:
    result = await client.get_available_assignees(fresh_wp)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_get_and_update_activity(
    client: OpenProjectClient, fresh_wp: int
) -> None:
    await client.add_work_package_comment(fresh_wp, "activity-test-comment")
    acts = await client.get_work_package_activities(fresh_wp)
    elements = acts.get("_embedded", {}).get("elements", [])
    # Find the comment activity
    comment_act = next(
        (
            a
            for a in elements
            if "activity-test-comment" in str(a.get("comment", {}).get("raw", ""))
        ),
        None,
    )
    assert comment_act, f"Comment activity not found: {elements}"
    act_id = comment_act.get("id")
    assert act_id

    try:
        updated = await client.update_activity(act_id, "activity-test-comment-updated")
        updated_raw = (
            updated.get("comment", {}).get("raw", "")
            if isinstance(updated, dict)
            else ""
        )
        assert (
            "activity-test-comment-updated" in updated_raw
        ), f"Activity not updated: {updated_raw!r}"
    except Exception as e:
        if "400" in str(e) or "403" in str(e):
            pytest.skip(f"update_activity requires 'edit journals' permission: {e}")
        raise
