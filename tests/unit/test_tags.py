#!/usr/bin/env python3
"""Verify that all @mcp.tool decorators carry a read or write tag."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def get_tools():
    os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
    os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
    from src.server import mcp

    tool_list = await mcp.list_tools()
    return {t.name: t for t in tool_list}


async def test_all_tools_have_tags():
    tools = await get_tools()
    missing = [name for name, t in tools.items() if not getattr(t, "tags", None)]
    assert not missing, f"Tools without tags: {missing}"
    print(f"✅ All {len(tools)} tools have tags")


async def test_tag_values():
    tools = await get_tools()
    # Every tool must have at least one access tag ("read" or "write")
    bad = [
        f"{name}:{t.tags}"
        for name, t in tools.items()
        if getattr(t, "tags", None) and not (t.tags & {"read", "write"})
    ]
    assert not bad, f"Tools missing an access tag (read/write): {bad}"
    print("✅ All tags have an access tag (read or write)")


async def assert_tag(tool_name: str, expected_tag: str, tools: dict):
    t = tools.get(tool_name)
    assert t is not None, f"Tool '{tool_name}' not found"
    assert expected_tag in (t.tags or set()), (
        f"Expected {tool_name} to have tag '{expected_tag}', got {t.tags}"
    )


async def test_connection_tags():
    tools = await get_tools()
    await assert_tag("test_connection", "read", tools)
    await assert_tag("check_permissions", "read", tools)
    print("✅ connection tags correct")


async def test_work_packages_tags():
    tools = await get_tools()
    read_tools = [
        "list_work_packages",
        "search_work_packages",
        "list_types",
        "list_statuses",
        "list_priorities",
        "list_work_package_activities",
        "list_overdue_work_packages",
        "list_work_packages_due_soon",
        "list_unassigned_work_packages",
        "list_work_packages_created_recently",
        "list_high_priority_work_packages",
        "list_work_packages_nearly_complete",
    ]
    write_tools = [
        "create_work_package",
        "update_work_package",
        "delete_work_package",
        "assign_work_package",
        "unassign_work_package",
        "add_work_package_comment",
    ]
    for name in read_tools:
        await assert_tag(name, "read", tools)
    for name in write_tools:
        await assert_tag(name, "write", tools)
    print(
        f"✅ work_packages tags correct ({len(read_tools)} read, {len(write_tools)} write)"
    )


async def test_projects_tags():
    tools = await get_tools()
    for name in ["list_projects", "get_project", "get_subprojects"]:
        await assert_tag(name, "read", tools)
    for name in [
        "create_project",
        "add_subproject",
        "update_project",
        "delete_project",
    ]:
        await assert_tag(name, "write", tools)
    print("✅ projects tags correct (3 read, 4 write)")


async def test_users_tags():
    tools = await get_tools()
    for name in [
        "list_users",
        "get_user",
        "list_roles",
        "get_role",
        "list_project_members",
        "list_user_projects",
    ]:
        await assert_tag(name, "read", tools)
    print("✅ users tags correct (6 read)")


async def test_memberships_tags():
    tools = await get_tools()
    for name in ["list_memberships", "get_membership"]:
        await assert_tag(name, "read", tools)
    for name in ["create_membership", "update_membership", "delete_membership"]:
        await assert_tag(name, "write", tools)
    print("✅ memberships tags correct (2 read, 3 write)")


async def test_hierarchy_relations_tags():
    tools = await get_tools()
    await assert_tag("list_work_package_children", "read", tools)
    for name in ["set_work_package_parent", "remove_work_package_parent"]:
        await assert_tag(name, "write", tools)
    for name in ["list_work_package_relations", "get_work_package_relation"]:
        await assert_tag(name, "read", tools)
    for name in [
        "create_work_package_relation",
        "update_work_package_relation",
        "delete_work_package_relation",
    ]:
        await assert_tag(name, "write", tools)
    print("✅ hierarchy + relations tags correct")


async def test_time_entries_versions_tags():
    tools = await get_tools()
    for name in ["list_time_entries", "list_time_entry_activities"]:
        await assert_tag(name, "read", tools)
    for name in ["create_time_entry", "update_time_entry", "delete_time_entry"]:
        await assert_tag(name, "write", tools)
    await assert_tag("list_versions", "read", tools)
    await assert_tag("create_version", "write", tools)
    print("✅ time_entries + versions tags correct")


async def test_reports_news_tags():
    tools = await get_tools()
    for name in [
        "generate_weekly_report",
        "generate_this_week_report",
        "generate_last_week_report",
        "get_report_data",
    ]:
        await assert_tag(name, "read", tools)
    for name in ["list_news", "get_news"]:
        await assert_tag(name, "read", tools)
    for name in ["create_news", "update_news", "delete_news"]:
        await assert_tag(name, "write", tools)
    print("✅ weekly_reports + news tags correct")


async def test_new_modules_tags():
    tools = await get_tools()
    # wiki
    await assert_tag("get_wiki_page", "read", tools)
    # groups
    for name in ["list_groups", "get_group"]:
        await assert_tag(name, "read", tools)
    # notifications
    await assert_tag("list_notifications", "read", tools)
    for name in ["mark_notification_read", "mark_all_notifications_read"]:
        await assert_tag(name, "write", tools)
    # attachments
    for name in ["list_attachments", "get_attachment"]:
        await assert_tag(name, "read", tools)
    for name in ["upload_attachment", "delete_attachment"]:
        await assert_tag(name, "write", tools)
    # budgets (cost entry endpoints don't exist in v3 API; tools removed)
    for name in ["list_budgets", "get_budget"]:
        await assert_tag(name, "read", tools)
    # Phase E — users (new), placeholder_users, preferences
    for name in ["list_principals", "get_my_preferences"]:
        await assert_tag(name, "read", tools)
    for name in ["create_user", "update_user"]:
        await assert_tag(name, "write", tools)
        await assert_tag(name, "admin", tools)
    for name in ["list_placeholder_users", "get_placeholder_user"]:
        await assert_tag(name, "read", tools)
    for name in ["create_placeholder_user", "update_placeholder_user"]:
        await assert_tag(name, "write", tools)
    await assert_tag("delete_placeholder_user", "write", tools)
    await assert_tag("delete_placeholder_user", "admin", tools)
    await assert_tag("update_my_preferences", "write", tools)
    # admin tag on projects
    for name in ["create_project", "delete_project"]:
        await assert_tag(name, "admin", tools)
    print(
        "✅ new module tags correct (wiki/groups/notifications/attachments/budgets/phase-e)"
    )


async def test_full_sweep():
    """Every tool: exactly one access tag, exactly one resource tag, >=1 matching
    composite, and every composite's prefix equals the tool's resource."""
    tools = await get_tools()

    ACCESS = {"read", "write"}

    def is_composite(t: str) -> bool:
        return t.endswith("-read") or t.endswith("-write")

    missing = [name for name, t in tools.items() if not getattr(t, "tags", None)]
    assert not missing, f"Tools without tags: {sorted(missing)}"

    wrong_access = [
        f"{name}:{sorted(t.tags)}"
        for name, t in tools.items()
        if len(t.tags & ACCESS) != 1
    ]
    assert not wrong_access, f"Tools without exactly one access tag: {wrong_access}"

    bad = []
    for name, t in tools.items():
        tags = set(t.tags)
        access = next(iter(tags & ACCESS))  # the single access tag
        composites = {x for x in tags if is_composite(x)}
        resources = {
            x
            for x in tags
            if x not in ACCESS and not is_composite(x) and x != "admin" and x != name
        }

        # exactly one resource tag
        if len(resources) != 1:
            bad.append(
                f"{name}: expected exactly one resource tag, found "
                f"{sorted(resources)} in {sorted(tags)}"
            )
            continue

        # >=1 composite whose suffix matches the access tag
        matching = {c for c in composites if c.endswith(f"-{access}")}
        if not matching:
            bad.append(f"{name}: no {access}-suffixed composite in {sorted(tags)}")
            continue

        # every composite's prefix must equal one of the tool's resources,
        # and every composite's suffix must equal the access tag
        for c in composites:
            prefix, _, suffix = c.rpartition("-")
            if suffix != access:
                bad.append(f"{name}: composite {c} suffix != access {access}")
            if prefix not in resources:
                bad.append(
                    f"{name}: composite {c} prefix not a resource {sorted(resources)}"
                )

    assert not bad, "Tag invariant violations:\n" + "\n".join(bad)

    read_count = sum(1 for t in tools.values() if "read" in (t.tags or set()))
    write_count = sum(1 for t in tools.values() if "write" in (t.tags or set()))
    print(
        f"✅ Full sweep: {len(tools)} tools, {read_count} read, {write_count} write, "
        "resource+composite invariant holds"
    )
