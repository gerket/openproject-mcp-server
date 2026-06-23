"""Unit tests for the list_capabilities and describe_tool tools."""

import os

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

import types
from unittest.mock import AsyncMock

import pytest

from src.server import mcp
from src.tool_registry import all_tools
from src.tools.server_info import describe_tool, list_capabilities


@pytest.mark.asyncio
async def test_list_capabilities_has_required_sections():
    out = await list_capabilities()
    assert "## Active tools" in out
    assert "## Inactive tools" in out
    assert "## Tag reference" in out
    assert "OPENPROJECT_MCP_INCLUDE_TAGS" in out
    assert "OPENPROJECT_MCP_EXCLUDE_TAGS" in out


@pytest.mark.asyncio
async def test_list_capabilities_lists_a_known_tool():
    out = await list_capabilities()
    assert "list_work_packages" in out
    # The tools report themselves, too.
    assert "list_capabilities" in out
    assert "describe_tool" in out


@pytest.mark.asyncio
async def test_list_capabilities_groups_by_category():
    out = await list_capabilities()
    # Category headers are rendered as level-3 markdown headers.
    assert "### work-packages" in out


@pytest.mark.asyncio
async def test_list_capabilities_is_one_line_per_tool():
    # Each tool gets exactly one bullet line in the overview — its first
    # docstring line — never the full multi-line docstring. Guards against
    # regressing to a full-docstring dump.
    out = await list_capabilities()
    bullets = [
        ln for ln in out.splitlines() if ln.startswith("- **list_work_packages**")
    ]
    assert len(bullets) == 1
    # That single line carries the first docstring line and nothing after it.
    assert "List work packages (tasks) with advanced filtering" in bullets[0]


@pytest.mark.asyncio
async def test_describe_tool_returns_full_docstring():
    out = await describe_tool(["list_work_packages"])
    assert "list_work_packages" in out
    # A line beyond the first must appear (full docstring, not just summary).
    # list_work_packages documents its parameters over many lines.
    assert out.count("\n") > 5
    # Tags and status are reported.
    assert "Tags:" in out
    assert "Status:" in out


@pytest.mark.asyncio
async def test_describe_tool_handles_unknown_name():
    out = await describe_tool(["does_not_exist_zzz"])
    assert "does_not_exist_zzz" in out
    assert "not found" in out.lower()


@pytest.mark.asyncio
async def test_describe_tool_handles_multiple_names():
    out = await describe_tool(["list_work_packages", "create_work_package"])
    assert "list_work_packages" in out
    assert "create_work_package" in out


@pytest.mark.asyncio
async def test_list_capabilities_with_inactive_tools(monkeypatch):
    """Exercise inactive-tool rendering when a filter excludes a tool."""
    registry = all_tools()
    # Pick a known tool to exclude.
    excluded = "create_user"
    assert excluded in registry, f"{excluded} must exist in registry for this test"

    # Build a fake active list that excludes create_user.
    fake_active = [
        types.SimpleNamespace(name=name) for name in registry if name != excluded
    ]
    mock_list_tools = AsyncMock(return_value=fake_active)
    monkeypatch.setattr(mcp, "list_tools", mock_list_tools)

    out = await list_capabilities()

    # The excluded tool should appear under the Inactive section.
    assert "## Inactive tools" in out
    assert "_All installed tools are active._" not in out
    assert f"**{excluded}**" in out

    # The inactive entry should include its tags in the exact format: _(tags: ...)_
    assert "_(tags:" in out
    # Confirm create_user's line has the tag marker.
    lines = out.splitlines()
    create_user_lines = [ln for ln in lines if f"**{excluded}**" in ln]
    assert len(create_user_lines) == 1, f"Expected exactly one line for {excluded}"
    assert "_(tags:" in create_user_lines[0]


@pytest.mark.asyncio
async def test_describe_tool_inactive_status(monkeypatch):
    """Exercise describe_tool for an inactive (filtered-out) tool."""
    registry = all_tools()
    excluded = "delete_project"
    assert excluded in registry, f"{excluded} must exist in registry for this test"

    # Build a fake active list that excludes delete_project.
    fake_active = [
        types.SimpleNamespace(name=name) for name in registry if name != excluded
    ]
    mock_list_tools = AsyncMock(return_value=fake_active)
    monkeypatch.setattr(mcp, "list_tools", mock_list_tools)

    out = await describe_tool([excluded])

    # The output should contain the exact status string from the code.
    assert f"## {excluded}" in out
    assert "**Status:** inactive (filtered out)" in out
    # The tool's full docstring should be present.
    info = registry[excluded]
    # At least the first line of the docstring should be there.
    first_line = info.doc.split("\n", 1)[0].strip()
    assert first_line in out
