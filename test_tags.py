#!/usr/bin/env python3
"""Verify that all @mcp.tool decorators carry a read or write tag."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def get_tools():
    os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
    os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
    from src.server import mcp
    return await mcp.get_tools()


async def test_all_tools_have_tags():
    tools = await get_tools()
    missing = [name for name, t in tools.items() if not getattr(t, "tags", None)]
    assert not missing, f"Tools without tags: {missing}"
    print(f"✅ All {len(tools)} tools have tags")


async def test_tag_values():
    tools = await get_tools()
    bad = [
        f"{name}:{t.tags}"
        for name, t in tools.items()
        if getattr(t, "tags", None) and t.tags - {"read", "write"}
    ]
    assert not bad, f"Tools with unexpected tag values: {bad}"
    print("✅ All tags are 'read' or 'write'")


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
        "list_work_packages", "search_work_packages", "list_types",
        "list_statuses", "list_priorities", "list_work_package_activities",
        "list_overdue_work_packages", "list_work_packages_due_soon",
        "list_unassigned_work_packages", "list_work_packages_created_recently",
        "list_high_priority_work_packages", "list_work_packages_nearly_complete",
    ]
    write_tools = [
        "create_work_package", "update_work_package", "delete_work_package",
        "assign_work_package", "unassign_work_package", "add_work_package_comment",
    ]
    for name in read_tools:
        await assert_tag(name, "read", tools)
    for name in write_tools:
        await assert_tag(name, "write", tools)
    print(f"✅ work_packages tags correct ({len(read_tools)} read, {len(write_tools)} write)")


async def test_projects_tags():
    tools = await get_tools()
    for name in ["list_projects", "get_project", "get_subprojects"]:
        await assert_tag(name, "read", tools)
    for name in ["create_project", "add_subproject", "update_project", "delete_project"]:
        await assert_tag(name, "write", tools)
    print("✅ projects tags correct (3 read, 4 write)")


async def test_users_tags():
    tools = await get_tools()
    for name in ["list_users", "get_user", "list_roles", "get_role",
                 "list_project_members", "list_user_projects"]:
        await assert_tag(name, "read", tools)
    print("✅ users tags correct (6 read)")


async def test_memberships_tags():
    tools = await get_tools()
    for name in ["list_memberships", "get_membership"]:
        await assert_tag(name, "read", tools)
    for name in ["create_membership", "update_membership", "delete_membership"]:
        await assert_tag(name, "write", tools)
    print("✅ memberships tags correct (2 read, 3 write)")


if __name__ == "__main__":
    asyncio.run(test_connection_tags())
    asyncio.run(test_work_packages_tags())
    asyncio.run(test_projects_tags())
    asyncio.run(test_users_tags())
    asyncio.run(test_memberships_tags())
    print("\n(Full tag sweep will pass once all modules are tagged)")
