"""
OpenProject MCP Server - FastMCP Implementation

Main server file that initializes FastMCP and registers all tools.
"""

import os
import logging
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
mcp = FastMCP(
    name="openproject-mcp"
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

    _client = OpenProjectClient(
        base_url=base_url,
        api_key=api_key,
        proxy=proxy
    )

    logger.info(f"✅ OpenProject MCP Server initialized")
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
    from src.tools import connection      # 2 tools
    from src.tools import work_packages   # 18 tools (list, search, create, update, delete, assign, unassign, comment, activities, types, statuses, priorities, overdue, due_soon, unassigned, recently_created, high_priority, nearly_complete)
    from src.tools import projects        # 7 tools (list, get, create, add_subproject, get_subprojects, update, delete)
    from src.tools import users           # 6 tools
    from src.tools import memberships     # 5 tools
    from src.tools import hierarchy       # 3 tools
    from src.tools import relations       # 5 tools
    from src.tools import time_entries    # 5 tools
    from src.tools import versions        # 2 tools
    from src.tools import weekly_reports  # 4 tools
    from src.tools import news            # 5 tools
    from src.tools import wiki            # 1 tool (API v3 wiki is a stub — only GET by integer ID)
    from src.tools import groups          # 2 tools
    from src.tools import notifications   # 3 tools
    from src.tools import attachments     # 4 tools
    from src.tools import costs           # 5 tools

    logger.info("✅ All 77 tools loaded successfully (45 read, 32 write)")
except ImportError as e:
    logger.warning(f"⚠️  Some tool modules failed to import: {e}")
    raise


def main() -> None:
    """Stdio entrypoint for `openproject-mcp` CLI script."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

