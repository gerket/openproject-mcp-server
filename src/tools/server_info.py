"""Help / discovery tools for AI assistants.

`list_capabilities` gives a lean overview of every tool (active and inactive)
with a one-line summary each; `describe_tool` returns the full docstring, tags,
and active/inactive status for named tools — the only way to inspect an
inactive tool, whose schema the client never received.
"""

from src.server import mcp
from src.tool_registry import all_tools, tracked_tool
from src.utils.formatting import format_error

# Category tags in priority order; a tool is grouped under the first one
# it carries. Anything else falls into "other".
_CATEGORY_ORDER = [
    "work-packages",
    "projects",
    "users",
    "queries",
    "storage",
    "time",
    "content",
    "notifications",
    "reports",
    "finance",
    "system",
]

_TAG_REFERENCE = """\
## Tag reference

**Access tags** (exactly one per tool):
- `read` — does not modify data
- `write` — creates, updates, or deletes data

**Tier tags:**
- `core` / `core-read` / `core-write` — everyday operations
- `situational` / `situational-read` / `situational-write` — less common operations
- `admin` — requires OpenProject administrator privileges

**Category tags:** `work-packages`, `projects`, `users`, `queries`, \
`storage`, `time`, `content`, `notifications`, `reports`, `finance`, `system`.

Each tool also carries a tag equal to its own name. Call `describe_tool` for \
the full documentation of any tool, including inactive ones.
"""

_CONFIG_EXAMPLES = """\
## Filtering configuration

Control which tools are active with environment variables (comma-separated tags):

- `OPENPROJECT_MCP_INCLUDE_TAGS` — if set, ONLY tools carrying one of these \
tags are active.
- `OPENPROJECT_MCP_EXCLUDE_TAGS` — tools carrying any of these tags are \
disabled (applied after include).

Examples:

```
# Read-only server
OPENPROJECT_MCP_INCLUDE_TAGS=read

# Everyday work-package + project tools, no admin
OPENPROJECT_MCP_INCLUDE_TAGS=work-packages,projects
OPENPROJECT_MCP_EXCLUDE_TAGS=admin

# Everything except destructive admin operations
OPENPROJECT_MCP_EXCLUDE_TAGS=admin
```
"""


def _category_of(tags: frozenset[str]) -> str:
    for category in _CATEGORY_ORDER:
        if category in tags:
            return category
    return "other"


def _first_line(doc: str) -> str:
    return doc.split("\n", 1)[0].strip() if doc else ""


@tracked_tool(tags={"read", "system", "system-read", "list_capabilities"})
async def list_capabilities() -> str:
    """Summarize this server's tools and how to filter them.

    Returns a markdown overview of the currently active tools (grouped by
    category, one line each), the tools that are installed but inactive due
    to tag filtering, a reference for what the tags mean, and examples for
    the OPENPROJECT_MCP_INCLUDE_TAGS / OPENPROJECT_MCP_EXCLUDE_TAGS
    environment variables. Call describe_tool for full details on any tool.
    """
    try:
        registry = all_tools()
        active_names = {t.name for t in await mcp.list_tools()}

        # Group active tools by category.
        groups: dict[str, list[str]] = {}
        for name in sorted(active_names):
            info = registry.get(name)
            tags = info.tags if info else frozenset()
            groups.setdefault(_category_of(tags), []).append(name)

        lines = [
            f"# OpenProject MCP server — {len(active_names)} active tool(s)",
            "",
            "## Active tools",
            "",
        ]
        ordered = [c for c in _CATEGORY_ORDER if c in groups]
        ordered += sorted(c for c in groups if c not in _CATEGORY_ORDER)
        for category in ordered:
            lines.append(f"### {category}")
            for name in groups[category]:
                info = registry.get(name)
                summary = _first_line(info.doc) if info else ""
                lines.append(f"- **{name}** — {summary}")
            lines.append("")

        # Inactive = registered but not active.
        inactive = sorted(set(registry) - active_names)
        lines.append("## Inactive tools")
        lines.append("")
        if not inactive:
            lines.append("_All installed tools are active._")
        else:
            lines.append(
                "Installed but disabled by the current tag filter "
                "(use describe_tool for details):"
            )
            lines.append("")
            for name in inactive:
                info = registry[name]
                summary = _first_line(info.doc)
                tag_list = ", ".join(f"`{t}`" for t in sorted(info.tags))
                lines.append(f"- **{name}** — {summary} _(tags: {tag_list})_")
        lines.append("")

        lines.append(_TAG_REFERENCE)
        lines.append(_CONFIG_EXAMPLES)

        return "\n".join(lines)
    except Exception as e:
        return format_error(f"Failed to build capability report: {e!s}")


@tracked_tool(tags={"read", "system", "system-read", "describe_tool"})
async def describe_tool(tool_names: list[str]) -> str:
    """Return full documentation for one or more tools by name.

    For each requested tool name, reports its active/inactive status, its
    tags, and its complete docstring. Works for inactive (tag-filtered)
    tools too — this is the only way to read their documentation, since the
    client never received their schema. Unknown names are reported as not
    found rather than failing the whole call. Use list_capabilities first to
    discover tool names.
    """
    try:
        registry = all_tools()
        active_names = {t.name for t in await mcp.list_tools()}

        sections: list[str] = []
        for name in tool_names:
            info = registry.get(name)
            if info is None:
                sections.append(f"## {name}\n\n_Tool not found._")
                continue
            status = "active" if name in active_names else "inactive (filtered out)"
            tag_list = ", ".join(f"`{t}`" for t in sorted(info.tags))
            doc = info.doc or "_No documentation._"
            sections.append(
                f"## {name}\n\n**Status:** {status}\n\n**Tags:** {tag_list}\n\n{doc}"
            )

        return "\n\n---\n\n".join(sections)
    except Exception as e:
        return format_error(f"Failed to describe tools: {e!s}")
