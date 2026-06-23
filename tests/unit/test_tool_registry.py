"""Unit tests for the tracked_tool registry shim."""

import os

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

from src.tool_registry import all_tools, tracked_tool


def test_tracked_tool_records_name_tags_and_doc():
    @tracked_tool(tags={"read", "system", "registry_probe_one"})
    async def registry_probe_one() -> str:
        """First line of probe.

        Second line that completes the thought.
        """
        return "ok"

    registry = all_tools()
    assert "registry_probe_one" in registry
    info = registry["registry_probe_one"]
    assert info.tags == frozenset({"read", "system", "registry_probe_one"})
    # Full docstring is kept, not just the first line.
    assert "First line of probe." in info.doc
    assert "completes the thought" in info.doc


def test_tracked_tool_uses_explicit_name_kwarg():
    @tracked_tool(name="explicit_probe_name", tags={"read", "system"})
    async def some_other_fn() -> str:
        """Probe with explicit name."""
        return "ok"

    registry = all_tools()
    assert "explicit_probe_name" in registry
    assert "some_other_fn" not in registry


def test_tracked_tool_returns_callable():
    @tracked_tool(tags={"read", "system", "registry_probe_two"})
    async def registry_probe_two() -> str:
        """Probe two."""
        return "ok"

    # mcp.tool returns a FunctionTool; the decorated object must be truthy
    # and not None (i.e. delegation happened).
    assert registry_probe_two is not None


def test_registry_covers_all_active_tools():
    import asyncio

    from src.server import mcp

    active = {t.name for t in asyncio.run(mcp.list_tools())}
    registry = set(all_tools().keys())
    # With no tag filter set, every active tool must be in the registry.
    missing = active - registry
    assert not missing, f"Active tools not tracked: {sorted(missing)}"
    # Spot-check a known tool came through conversion.
    assert "list_work_packages" in registry
