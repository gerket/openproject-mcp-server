"""Unit tests for the list_capabilities and describe_tool tools."""

import os

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

import pytest

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
