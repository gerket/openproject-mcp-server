"""Wiki page tools for OpenProject.

The OpenProject v3 API wiki support is currently a stub: only a single
GET endpoint exists — GET /api/v3/wiki_pages/{id} — identified by integer
ID. List, create, update, and delete operations are not available in the
API. This module exposes the one real endpoint.
"""

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_wiki_page_detail


@mcp.tool(tags={"read", "content", "situational", "situational-read", "get_wiki_page"})
async def get_wiki_page(wiki_page_id: int) -> str:
    """Get a wiki page by its integer ID, including full Markdown content.

    Note: The OpenProject v3 API only supports fetching wiki pages by
    integer ID. To discover page IDs, navigate to the wiki in the
    OpenProject UI and note the page ID from the URL or page properties.

    Args:
        wiki_page_id: The wiki page integer ID

    Returns:
        Full wiki page content in Markdown
    """
    try:
        client = get_client()
        page = await client.get_wiki_page_by_id(wiki_page_id)
        return format_wiki_page_detail(page)
    except Exception as e:
        return format_error(f"Failed to get wiki page: {e!s}")
