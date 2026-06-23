"""Registry shim that tracks every tool at decoration time.

FastMCP's `mcp.list_tools()` returns only tools left active after tag
filtering, and FastMCP 3.x exposes no public API to enumerate disabled
tools. To let `list_capabilities` report filtered-out tools, `tracked_tool`
wraps `mcp.tool` and records each tool in `_ALL_TOOLS` before any filtering
is applied.

`mcp` is imported lazily inside `tracked_tool` to avoid the import cycle:
`src.server` imports the tool modules, which import this module.
"""

import inspect
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolInfo:
    """A tool's identity as captured at decoration time."""

    name: str
    tags: frozenset[str]
    doc: str  # full docstring; consumers take the first line for summaries


_ALL_TOOLS: dict[str, ToolInfo] = {}


def tracked_tool(*args: Any, **kwargs: Any):
    """Drop-in replacement for `@mcp.tool` that also records the tool.

    Accepts the same arguments as `mcp.tool`. Records the decorated
    function's name (the `name` kwarg if given, else `fn.__name__`), its
    `tags`, and its full docstring into `_ALL_TOOLS`, then delegates to
    `mcp.tool` and returns its result unchanged.
    """
    from src.server import mcp  # lazy import to avoid cycle

    def decorator(fn):
        name = kwargs.get("name") or fn.__name__
        tags = frozenset(kwargs.get("tags") or set())
        doc = inspect.getdoc(fn) or ""
        _ALL_TOOLS[name] = ToolInfo(name=name, tags=tags, doc=doc)
        return mcp.tool(*args, **kwargs)(fn)

    return decorator


def all_tools() -> dict[str, ToolInfo]:
    """Return a copy of the full tool registry, keyed by tool name."""
    return dict(_ALL_TOOLS)
