#!/usr/bin/env python3
"""Live integration tests against a real OpenProject instance.

Run with:
    OPENPROJECT_URL=https://your-instance OPENPROJECT_API_KEY=your-token uv run python test_live_integration.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

results: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))
    status = "✅" if passed else "❌"
    print(f"{status} {name}" + (f": {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


async def run_tests(base_url: str, api_key: str) -> None:
    from src.client import OpenProjectClient

    client = OpenProjectClient(base_url=base_url, api_key=api_key)

    # ------------------------------------------------------------------ #
    # CONNECTION
    # ------------------------------------------------------------------ #
    section("Connection")

    try:
        result = await client.test_connection()
        assert (
            "instanceVersion" in result or "_type" in result or "coreVersion" in result
        )
        record(
            "connection/test_connection",
            True,
            f"version={result.get('instanceVersion', 'N/A')}",
        )
    except Exception as e:
        record("connection/test_connection", False, str(e)[:120])

    try:
        result = await client.check_permissions()
        assert result  # non-empty
        record(
            "connection/check_permissions", True, f"user={result.get('name', 'N/A')}"
        )
    except Exception as e:
        record("connection/check_permissions", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # PROJECTS
    # ------------------------------------------------------------------ #
    section("Projects")

    try:
        result = await client.get_projects()
        elements = result.get("_embedded", {}).get("elements", [])
        record("projects/list_projects", True, f"count={len(elements)}")
    except Exception as e:
        record("projects/list_projects", False, str(e)[:120])

    try:
        result = await client.get_project(4)
        assert result.get("name"), "No name in project response"
        record("projects/get_project_4", True, f"name={result['name']}")
    except Exception as e:
        record("projects/get_project_4", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # WORK PACKAGES
    # ------------------------------------------------------------------ #
    section("Work Packages")

    try:
        result = await client.get_work_packages(project_id=4, page_size=5)
        elements = result.get("_embedded", {}).get("elements", [])
        record("work_packages/list_project_4", True, f"count={len(elements)}")
    except Exception as e:
        record("work_packages/list_project_4", False, str(e)[:120])

    try:
        result = await client.get_work_package(46)
        assert (
            result.get("subject") == "test"
        ), f"Expected subject='test', got '{result.get('subject')}'"
        record("work_packages/get_wp_46", True, f"subject={result['subject']}")
    except Exception as e:
        record("work_packages/get_wp_46", False, str(e)[:120])

    temp_wp_id = None
    try:
        result = await client.create_work_package(
            {"project": 4, "subject": "integration-test-temp", "type": 1}
        )
        temp_wp_id = result.get("id")
        assert temp_wp_id, "No ID in created WP"
        record("work_packages/create_temp", True, f"id={temp_wp_id}")
    except Exception as e:
        record("work_packages/create_temp", False, str(e)[:120])

    if temp_wp_id:
        try:
            result = await client.update_work_package(
                temp_wp_id, {"description": "integration test description"}
            )
            record("work_packages/update_temp", True)
        except Exception as e:
            record("work_packages/update_temp", False, str(e)[:120])

        try:
            ok = await client.delete_work_package(temp_wp_id)
            assert ok
            record("work_packages/delete_temp", True)
        except Exception as e:
            record("work_packages/delete_temp", False, str(e)[:120])
    else:
        record("work_packages/update_temp", False, "skipped: create_temp failed")
        record("work_packages/delete_temp", False, "skipped: create_temp failed")

    try:
        filters = json.dumps([{"subjectOrId": {"operator": "**", "values": ["test"]}}])
        result = await client.get_work_packages(filters=filters)
        elements = result.get("_embedded", {}).get("elements", [])
        assert len(elements) > 0, "Expected at least 1 result"
        record("work_packages/search", True, f"count={len(elements)}")
    except Exception as e:
        record("work_packages/search", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # CUSTOM FIELDS (on WP #46)
    # ------------------------------------------------------------------ #
    section("Custom Fields (WP #46)")

    # CF2: String
    try:
        await client.update_work_package(
            46, {"custom_fields": {"customField2": "cf2-test-string"}}
        )
        result = await client.get_work_package(46)
        val = result.get("customField2")
        assert val == "cf2-test-string", f"Expected 'cf2-test-string', got {val!r}"
        record("custom_fields/cf2_string", True)
    except Exception as e:
        record("custom_fields/cf2_string", False, str(e)[:120])

    # CF3: Formattable
    try:
        await client.update_work_package(
            46,
            {
                "custom_fields": {
                    "customField3": {"format": "markdown", "raw": "cf3 test text"}
                }
            },
        )
        result = await client.get_work_package(46)
        val = result.get("customField3")
        raw = val.get("raw", "") if isinstance(val, dict) else str(val)
        assert "cf3 test text" in raw, f"Expected text in CF3, got {val!r}"
        record("custom_fields/cf3_formattable", True)
    except Exception as e:
        record("custom_fields/cf3_formattable", False, str(e)[:120])

    # CF4: Boolean
    try:
        await client.update_work_package(46, {"custom_fields": {"customField4": True}})
        result = await client.get_work_package(46)
        val = result.get("customField4")
        assert val is True, f"Expected True, got {val!r}"
        record("custom_fields/cf4_boolean", True)
    except Exception as e:
        record("custom_fields/cf4_boolean", False, str(e)[:120])

    # CF5: Date
    try:
        await client.update_work_package(
            46, {"custom_fields": {"customField5": "2026-06-19"}}
        )
        result = await client.get_work_package(46)
        val = result.get("customField5")
        assert val == "2026-06-19", f"Expected date, got {val!r}"
        record("custom_fields/cf5_date", True)
    except Exception as e:
        record("custom_fields/cf5_date", False, str(e)[:120])

    # CF6: Float
    try:
        await client.update_work_package(46, {"custom_fields": {"customField6": 3.14}})
        result = await client.get_work_package(46)
        val = result.get("customField6")
        assert val is not None, "Expected float value, got None"
        record("custom_fields/cf6_float", True, f"val={val}")
    except Exception as e:
        record("custom_fields/cf6_float", False, str(e)[:120])

    # CF7: SKIP — needs admin setup
    record("custom_fields/cf7", True, "SKIP: needs admin setup")

    # CF8: Integer
    try:
        await client.update_work_package(46, {"custom_fields": {"customField8": 42}})
        result = await client.get_work_package(46)
        val = result.get("customField8")
        assert val is not None, "Expected integer value, got None"
        record("custom_fields/cf8_integer", True, f"val={val}")
    except Exception as e:
        record("custom_fields/cf8_integer", False, str(e)[:120])

    # CF9: Link (URL string)
    try:
        await client.update_work_package(
            46, {"custom_fields": {"customField9": "https://example.com"}}
        )
        result = await client.get_work_package(46)
        val = result.get("customField9")
        assert val is not None, "Expected URL value, got None"
        record("custom_fields/cf9_link", True, f"val={val}")
    except Exception as e:
        record("custom_fields/cf9_link", False, str(e)[:120])

    # CF10: SKIP — needs admin setup
    record("custom_fields/cf10", True, "SKIP: needs admin setup")

    # CF11: String
    try:
        await client.update_work_package(
            46, {"custom_fields": {"customField11": "cf11-test"}}
        )
        result = await client.get_work_package(46)
        val = result.get("customField11")
        assert val == "cf11-test", f"Expected 'cf11-test', got {val!r}"
        record("custom_fields/cf11_string", True)
    except Exception as e:
        record("custom_fields/cf11_string", False, str(e)[:120])

    # CF12: SKIP — needs admin setup
    record("custom_fields/cf12", True, "SKIP: needs admin setup")

    # CF14: SKIP — needs admin setup
    record("custom_fields/cf14", True, "SKIP: needs admin setup")

    # CF15: Formattable
    try:
        await client.update_work_package(
            46,
            {
                "custom_fields": {
                    "customField15": {"format": "markdown", "raw": "cf15 test text"}
                }
            },
        )
        result = await client.get_work_package(46)
        val = result.get("customField15")
        raw = val.get("raw", "") if isinstance(val, dict) else str(val)
        assert "cf15 test text" in raw, f"Expected text in CF15, got {val!r}"
        record("custom_fields/cf15_formattable", True)
    except Exception as e:
        record("custom_fields/cf15_formattable", False, str(e)[:120])

    # Cleanup: reset all CFs on WP #46
    try:
        await client.update_work_package(
            46,
            {
                "custom_fields": {
                    "customField2": None,
                    "customField4": None,
                    "customField5": None,
                    "customField6": None,
                    "customField8": None,
                    "customField9": None,
                    "customField11": None,
                }
            },
        )
        record("custom_fields/cleanup", True)
    except Exception as e:
        record("custom_fields/cleanup", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # GROUPS
    # ------------------------------------------------------------------ #
    section("Groups")

    try:
        result = await client.get_groups()
        elements = result.get("_embedded", {}).get(
            "elements", result.get("elements", [])
        )
        record("groups/list_groups", True, f"count={len(elements)}")
    except Exception as e:
        record("groups/list_groups", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # NOTIFICATIONS
    # ------------------------------------------------------------------ #
    section("Notifications")

    try:
        result = await client.get_notifications(page_size=5)
        record("notifications/list", True, f"type={result.get('_type', 'N/A')}")
    except Exception as e:
        record("notifications/list", False, str(e)[:120])

    try:
        await client.mark_all_notifications_read()
        record("notifications/mark_all_read", True)
    except Exception as e:
        record("notifications/mark_all_read", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # ATTACHMENTS (on WP #46)
    # ------------------------------------------------------------------ #
    section("Attachments")

    attachment_id = None
    try:
        file_bytes = b"integration test attachment content"
        result = await client.upload_attachment(
            container_type="work_packages",
            container_id=46,
            file_bytes=file_bytes,
            filename="test-attachment.txt",
            content_type="text/plain",
        )
        attachment_id = result.get("id")
        assert attachment_id, "No attachment ID returned"
        record("attachments/upload", True, f"id={attachment_id}")
    except Exception as e:
        record("attachments/upload", False, str(e)[:120])

    if attachment_id:
        try:
            result = await client.list_attachments("work_packages", 46)
            elements = result.get("_embedded", {}).get("elements", [])
            assert len(elements) >= 1, f"Expected >= 1 attachment, got {len(elements)}"
            record("attachments/list", True, f"count={len(elements)}")
        except Exception as e:
            record("attachments/list", False, str(e)[:120])

        try:
            result = await client.get_attachment(attachment_id)
            assert result.get("id") == attachment_id
            record("attachments/get", True)
        except Exception as e:
            record("attachments/get", False, str(e)[:120])

        try:
            ok = await client.delete_attachment(attachment_id)
            assert ok
            record("attachments/delete", True)
        except Exception as e:
            record("attachments/delete", False, str(e)[:120])
    else:
        record("attachments/list", False, "skipped: upload failed")
        record("attachments/get", False, "skipped: upload failed")
        record("attachments/delete", False, "skipped: upload failed")

    # ------------------------------------------------------------------ #
    # TIME ENTRIES
    # ------------------------------------------------------------------ #
    section("Time Entries")

    before_count = 0
    try:
        filters = json.dumps([{"project": {"operator": "=", "values": ["4"]}}])
        result = await client.get_time_entries(filters=filters)
        elements = result.get("_embedded", {}).get("elements", [])
        before_count = len(elements)
        record("time_entries/list_project_4", True, f"count={before_count}")
    except Exception as e:
        record("time_entries/list_project_4", False, str(e)[:120])

    entry_id = None
    try:
        result = await client.create_time_entry(
            {
                "work_package_id": 46,
                "hours": 0.5,
                "spent_on": "2026-06-19",
                "activity_id": 1,
            }
        )
        entry_id = result.get("id")
        assert entry_id, "No ID in created time entry"
        record("time_entries/create", True, f"id={entry_id}")
    except Exception as e:
        record("time_entries/create", False, str(e)[:120])

    if entry_id:
        try:
            filters = json.dumps([{"project": {"operator": "=", "values": ["4"]}}])
            result = await client.get_time_entries(filters=filters)
            elements = result.get("_embedded", {}).get("elements", [])
            assert (
                len(elements) > before_count
            ), f"Expected count > {before_count}, got {len(elements)}"
            record("time_entries/list_after_create", True, f"count={len(elements)}")
        except Exception as e:
            record("time_entries/list_after_create", False, str(e)[:120])

        try:
            ok = await client.delete_time_entry(entry_id)
            assert ok
            record("time_entries/delete", True)
        except Exception as e:
            record("time_entries/delete", False, str(e)[:120])
    else:
        record("time_entries/list_after_create", False, "skipped: create failed")
        record("time_entries/delete", False, "skipped: create failed")

    # ------------------------------------------------------------------ #
    # VERSIONS
    # ------------------------------------------------------------------ #
    section("Versions")

    try:
        result = await client.get_versions(4)
        elements = result.get("_embedded", {}).get("elements", [])
        record("versions/list", True, f"count={len(elements)}")
    except Exception as e:
        record("versions/list", False, str(e)[:120])

    version_id = None
    try:
        result = await client.create_version(4, {"name": "Integration Test Version"})
        version_id = result.get("id")
        assert version_id, "No ID in created version"
        record("versions/create", True, f"id={version_id}")
    except Exception as e:
        record("versions/create", False, str(e)[:120])

    if version_id:
        try:
            result = await client.get_versions(4)
            elements = result.get("_embedded", {}).get("elements", [])
            assert len(elements) >= 1, f"Expected >= 1 version, got {len(elements)}"
            record("versions/list_after_create", True, f"count={len(elements)}")
        except Exception as e:
            record("versions/list_after_create", False, str(e)[:120])

        # Try to delete; if not supported, close it
        try:
            if hasattr(client, "delete_version"):
                await client.delete_version(version_id)
            else:
                await client._request(
                    "PATCH", f"/versions/{version_id}", {"status": "closed"}
                )
            record("versions/delete_or_close", True)
        except Exception as e:
            record("versions/delete_or_close", False, str(e)[:120])
    else:
        record("versions/list_after_create", False, "skipped: create failed")
        record("versions/delete_or_close", False, "skipped: create failed")

    # ------------------------------------------------------------------ #
    # MEMBERSHIPS
    # ------------------------------------------------------------------ #
    section("Memberships")

    try:
        result = await client.get_memberships(project_id=4)
        elements = result.get("_embedded", {}).get("elements", [])
        record("memberships/list_project_4", True, f"count={len(elements)}")

        if elements:
            first = elements[0]
            first_id = first.get("id")
            if first_id:
                try:
                    m = await client.get_membership(first_id)
                    record("memberships/get_first", True, f"id={first_id}")
                except Exception as e2:
                    record("memberships/get_first", False, str(e2)[:120])
            else:
                record("memberships/get_first", True, "SKIP: no membership ID")
        else:
            record("memberships/get_first", True, "SKIP: no memberships")
    except Exception as e:
        record("memberships/list_project_4", False, str(e)[:120])
        record("memberships/get_first", False, "skipped: list failed")

    # ------------------------------------------------------------------ #
    # USERS
    # ------------------------------------------------------------------ #
    section("Users")

    try:
        result = await client.get_users()
        elements = result.get("_embedded", {}).get("elements", [])
        record("users/list", True, f"count={len(elements)}")
    except Exception as e:
        record("users/list", False, str(e)[:120])

    try:
        result = await client.get_user(5)
        name = result.get("name", "")
        assert "Tom" in name, f"Expected 'Tom' in name, got {name!r}"
        record("users/get_5", True, f"name={name}")
    except Exception as e:
        record("users/get_5", False, str(e)[:120])

    # ------------------------------------------------------------------ #
    # NEWS
    # ------------------------------------------------------------------ #
    section("News")

    try:
        filters = json.dumps([{"project": {"operator": "=", "values": ["4"]}}])
        result = await client.get_news(filters=filters, page_size=5)
        elements = result.get("_embedded", {}).get("elements", [])
        record("news/list_project_4", True, f"count={len(elements)}")
    except Exception as e:
        record("news/list_project_4", False, str(e)[:120])

    news_id = None
    try:
        result = await client.create_news(
            {
                "project": 4,
                "title": "Integration Test News",
                "summary": "Created by integration test",
                "description": "This is a test news entry.",
            }
        )
        news_id = result.get("id")
        assert news_id, "No ID in created news"
        record("news/create", True, f"id={news_id}")
    except Exception as e:
        record("news/create", False, str(e)[:120])

    if news_id:
        try:
            result = await client.get_news_item(news_id)
            assert result.get("id") == news_id
            record("news/get", True)
        except Exception as e:
            record("news/get", False, str(e)[:120])

        try:
            result = await client.update_news(
                news_id, {"title": "Integration Test News (Updated)"}
            )
            # success if no exception
            record("news/update", True)
        except Exception as e:
            record("news/update", False, str(e)[:120])

        try:
            ok = await client.delete_news(news_id)
            assert ok
            record("news/delete", True)
        except Exception as e:
            record("news/delete", False, str(e)[:120])
    else:
        record("news/get", False, "skipped: create failed")
        record("news/update", False, "skipped: create failed")
        record("news/delete", False, "skipped: create failed")

    # ------------------------------------------------------------------ #
    # RELATIONS
    # ------------------------------------------------------------------ #
    section("Relations")

    wp_a_id = None
    wp_b_id = None

    try:
        result = await client.create_work_package(
            {"project": 4, "subject": "integration-test-relation-A", "type": 1}
        )
        wp_a_id = result.get("id")
        assert wp_a_id
        record("relations/create_wp_a", True, f"id={wp_a_id}")
    except Exception as e:
        record("relations/create_wp_a", False, str(e)[:120])

    try:
        result = await client.create_work_package(
            {"project": 4, "subject": "integration-test-relation-B", "type": 1}
        )
        wp_b_id = result.get("id")
        assert wp_b_id
        record("relations/create_wp_b", True, f"id={wp_b_id}")
    except Exception as e:
        record("relations/create_wp_b", False, str(e)[:120])

    relation_id = None
    if wp_a_id and wp_b_id:
        try:
            result = await client.create_work_package_relation(
                {"from_id": wp_a_id, "to_id": wp_b_id, "type": "relates"}
            )
            relation_id = result.get("id")
            assert relation_id
            record("relations/create_relation", True, f"id={relation_id}")
        except Exception as e:
            record("relations/create_relation", False, str(e)[:120])

        try:
            filters = json.dumps(
                [{"involved": {"operator": "=", "values": [str(wp_a_id)]}}]
            )
            result = await client.list_work_package_relations(filters)
            elements = result.get("_embedded", {}).get("elements", [])
            assert len(elements) >= 1, f"Expected >= 1 relation, got {len(elements)}"
            record("relations/list_relations", True, f"count={len(elements)}")
        except Exception as e:
            record("relations/list_relations", False, str(e)[:120])

        if relation_id:
            try:
                ok = await client.delete_work_package_relation(relation_id)
                assert ok
                record("relations/delete_relation", True)
            except Exception as e:
                record("relations/delete_relation", False, str(e)[:120])
        else:
            record(
                "relations/delete_relation", False, "skipped: create_relation failed"
            )
    else:
        record("relations/create_relation", False, "skipped: WP creation failed")
        record("relations/list_relations", False, "skipped: WP creation failed")
        record("relations/delete_relation", False, "skipped: WP creation failed")

    # Cleanup: delete both temp WPs
    cleanup_ok = True
    for wp_id in [wp_a_id, wp_b_id]:
        if wp_id:
            try:
                await client.delete_work_package(wp_id)
            except Exception:
                cleanup_ok = False
    record(
        "relations/cleanup_wps",
        cleanup_ok,
        "" if cleanup_ok else "some WP deletions failed",
    )

    # ------------------------------------------------------------------ #
    # CUSTOM ACTIONS
    # Requires at least one custom action configured in OpenProject admin.
    # See docs/integration-test-setup.md — "Custom action setup".
    # ------------------------------------------------------------------ #
    section("Custom Actions")

    action_id = None

    try:
        result = await client.list_custom_actions()
        actions = result.get("_embedded", {}).get("elements", [])
        if actions:
            action_id = actions[0].get("id")
        record(
            "custom_actions/list",
            len(actions) >= 1,
            f"count={len(actions)}"
            if actions
            else "SKIP: no actions found — see docs/integration-test-setup.md",
        )
    except Exception as e:
        record("custom_actions/list", False, str(e)[:120])

    if action_id:
        try:
            result = await client.get_custom_action(action_id)
            assert result.get("id") == action_id
            record(
                "custom_actions/get", True, f"id={action_id}, name={result.get('name')}"
            )
        except Exception as e:
            record("custom_actions/get", False, str(e)[:120])

        try:
            # Create a fresh WP in "New" status to execute the action against.
            # The "Start work" action (New → In Progress) is the documented test action.
            result = await client.create_work_package(
                {"project": 4, "subject": "integration-test-custom-action", "type": 1}
            )
            test_wp_id = result.get("id")
            assert test_wp_id
            record("custom_actions/create_test_wp", True, f"id={test_wp_id}")

            result = await client.execute_custom_action(action_id, test_wp_id)
            wp_after = result.get("_embedded", {}).get("workPackage", result)
            status_title = (
                wp_after.get("_links", {}).get("status", {}).get("title", "unknown")
            )
            record(
                "custom_actions/execute",
                True,
                f"action_id={action_id}, wp={test_wp_id}, status_after={status_title}",
            )

            # Cleanup
            await client.delete_work_package(test_wp_id)
        except Exception as e:
            record("custom_actions/execute", False, str(e)[:120])
    else:
        record("custom_actions/get", False, "skipped: no action found")
        record("custom_actions/execute", False, "skipped: no action found")

    # ------------------------------------------------------------------ #
    # VERSION LIFECYCLE (update + delete, extends existing create test)
    # ------------------------------------------------------------------ #
    section("Version lifecycle (update + delete)")

    v_id = None
    try:
        result = await client.create_version(
            4, {"name": "integration-test-version-lifecycle"}
        )
        v_id = result.get("id")
        assert v_id
        record("versions/lifecycle_create", True, f"id={v_id}")
    except Exception as e:
        record("versions/lifecycle_create", False, str(e)[:120])

    if v_id:
        try:
            result = await client.update_version(
                v_id, {"name": "integration-test-version-updated", "status": "locked"}
            )
            assert result.get("name") == "integration-test-version-updated"
            record(
                "versions/lifecycle_update",
                True,
                f"name={result.get('name')}, status={result.get('status')}",
            )
        except Exception as e:
            record("versions/lifecycle_update", False, str(e)[:120])

        try:
            ok = await client.delete_version(v_id)
            assert ok
            record("versions/lifecycle_delete", True, f"id={v_id} deleted")
        except Exception as e:
            record("versions/lifecycle_delete", False, str(e)[:120])
    else:
        record("versions/lifecycle_update", False, "skipped: create failed")
        record("versions/lifecycle_delete", False, "skipped: create failed")

    # ------------------------------------------------------------------ #
    # SUMMARY
    # ------------------------------------------------------------------ #
    print(f"\n{'=' * 60}")
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(results)}")

    if failed > 0:
        print("\nFailed tests:")
        for name, p, detail in results:
            if not p:
                print(f"  ❌ {name}: {detail}")
        sys.exit(1)
    else:
        print("All tests passed!")


def load_credentials() -> tuple[str, str]:
    """Return (base_url, api_key). Both must be set as environment variables."""
    base_url = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
    api_key = os.environ.get("OPENPROJECT_API_KEY", "")
    if not base_url:
        raise RuntimeError(
            "Set OPENPROJECT_URL env var (e.g. https://openproject.yourdomain.com)"
        )
    if not api_key:
        raise RuntimeError(
            "Set OPENPROJECT_API_KEY env var (your OpenProject API token)"
        )
    return base_url, api_key


def main() -> None:
    try:
        base_url, api_key = load_credentials()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    asyncio.run(run_tests(base_url, api_key))


if __name__ == "__main__":
    main()
