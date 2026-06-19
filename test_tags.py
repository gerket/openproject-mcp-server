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


if __name__ == "__main__":
    asyncio.run(test_connection_tags())
    print("\n(Full tag sweep will pass once all modules are tagged)")
