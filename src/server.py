"""
OpenProject MCP Server - FastMCP Implementation

Main server file that initializes FastMCP and registers all tools.
"""

import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from src.client import OpenProjectClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server


def _parse_tags(env_var: str) -> set[str] | None:
    """Parse comma-separated tags from an env var. Returns None if unset."""
    val = os.getenv(env_var, "").strip()
    if not val:
        return None
    return {t.strip() for t in val.split(",") if t.strip()}


mcp = FastMCP(
    name="openproject-mcp",
    include_tags=_parse_tags("OPENPROJECT_MCP_INCLUDE_TAGS"),
    exclude_tags=_parse_tags("OPENPROJECT_MCP_EXCLUDE_TAGS"),
)

# Initialize OpenProject client as global variable
_client = None

try:
    base_url = os.getenv("OPENPROJECT_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY")
    proxy = os.getenv("OPENPROJECT_PROXY")

    if not base_url or not api_key:
        raise ValueError(
            "Missing required environment variables: OPENPROJECT_URL and OPENPROJECT_API_KEY must be set"
        )

    _client = OpenProjectClient(base_url=base_url, api_key=api_key, proxy=proxy)

    logger.info("✅ OpenProject MCP Server initialized")
    logger.info(f"   Server: {base_url}")
    logger.info(f"   Proxy: {proxy if proxy else 'None'}")

except Exception as e:
    logger.error(f"❌ Failed to initialize OpenProject client: {e}")
    raise


# Dependency injection helper for tools
def get_client():
    """Get OpenProject client instance."""
    return _client


# Import ALL tool modules (decorators auto-register tools)
logger.info("Loading tool modules...")

try:
    from src.tools import (  # noqa: F401
        attachments,  # 4 tools
        connection,  # 2 tools
        costs,  # 5 tools
        groups,  # 2 tools
        hierarchy,  # 3 tools
        memberships,  # 5 tools
        news,  # 5 tools
        notifications,  # 3 tools
        projects,  # 7 tools (list, get, create, add_subproject, get_subprojects, update, delete)
        queries,  # 8 tools: list_queries, get_query, get_default_query, create_query, update_query, delete_query, star_query, unstar_query
        relations,  # 5 tools
        reminders,  # 2 tools: list_reminders, create_reminder
        time_entries,  # 5 tools
        users,  # 6 tools
        versions,  # 2 tools
        watchers,  # 7 tools: list_watchers, list_available_watchers, add_watcher, remove_watcher, get_activity, update_activity, list_available_assignees
        weekly_reports,  # 4 tools
        wiki,  # 1 tool (API v3 wiki is a stub — only GET by integer ID)
        work_packages,  # 18 tools (list, search, create, update, delete, assign, unassign, comment, activities, types, statuses, priorities, overdue, due_soon, unassigned, recently_created, high_priority, nearly_complete)
    )

    _tool_map: dict = getattr(getattr(mcp, "_tool_manager", None), "_tools", {})
    _read = sum(1 for t in _tool_map.values() if "read" in (t.tags or set()))
    _write = sum(1 for t in _tool_map.values() if "write" in (t.tags or set()))
    logger.info(
        "✅ All %d tools loaded successfully (%d read, %d write)",
        len(_tool_map),
        _read,
        _write,
    )
except ImportError as e:
    logger.warning(f"⚠️  Some tool modules failed to import: {e}")
    raise


def main() -> None:
    """Stdio entrypoint for `openproject-mcp` CLI script."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
