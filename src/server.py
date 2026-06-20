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


mcp = FastMCP(name="openproject-mcp")

_include_tags = _parse_tags("OPENPROJECT_MCP_INCLUDE_TAGS")
_exclude_tags = _parse_tags("OPENPROJECT_MCP_EXCLUDE_TAGS")
if _include_tags:
    mcp.enable(tags=_include_tags, only=True)
if _exclude_tags:
    mcp.disable(tags=_exclude_tags)

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

# Import all tool modules — decorators auto-register tools with the MCP server.
# Any ImportError propagates immediately; no silent partial loading.
from src.tools import (  # noqa: F401, E402
    attachments,  # 4 tools
    categories,  # 2 tools: list_categories, get_category
    connection,  # 2 tools
    costs,  # 2 tools: list_budgets, get_budget (budget read endpoints only — cost entries not in v3 API)
    custom_actions,  # 3 tools: list_custom_actions, get_custom_action, execute_custom_action
    documents,  # 3 tools: list_documents, get_document, update_document
    groups,  # 2 tools
    hierarchy,  # 3 tools
    memberships,  # 5 tools
    news,  # 5 tools
    notifications,  # 3 tools
    placeholder_users,  # 5 tools: list, get, create, update, delete_placeholder_user
    projects,  # 7 tools (list, get, create[admin], add_subproject, get_subprojects, update, delete[admin])
    queries,  # 8 tools: list_queries, get_query, get_default_query, create_query, update_query, delete_query, star_query, unstar_query
    relations,  # 5 tools
    reminders,  # 2 tools: list_reminders, create_reminder
    storages,  # 7 tools: list_storages, get_storage, list_project_storages, list/get/create/delete file links
    time_entries,  # 5 tools
    users,  # 11 tools: list_users, get_user, list_roles, get_role, list_project_members, list_user_projects, list_principals, create_user[admin], update_user[admin], get_my_preferences, update_my_preferences
    versions,  # 4 tools: list_versions, create_version, update_version, delete_version
    views,  # 2 tools: list_views, get_view
    watchers,  # 7 tools: list_watchers, list_available_watchers, add_watcher, remove_watcher, get_activity, update_activity, list_available_assignees
    weekly_reports,  # 4 tools
    wiki,  # 1 tool (API v3 wiki is a stub — only GET by integer ID)
    work_packages,  # 18 tools (list, search, create, update, delete, assign, unassign, comment, activities, types, statuses, priorities, overdue, due_soon, unassigned, recently_created, high_priority, nearly_complete)
)

_tool_list = list(mcp.local_provider._components.values())
_read = sum(1 for t in _tool_list if "read" in (t.tags or set()))
_write = sum(1 for t in _tool_list if "write" in (t.tags or set()))
logger.info(
    "✅ All %d tools loaded successfully (%d read, %d write)",
    len(_tool_list),
    _read,
    _write,
)


def main() -> None:
    """Stdio entrypoint for `openproject-mcp` CLI script."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
