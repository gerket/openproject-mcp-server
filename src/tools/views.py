"""View tools (Phase G).

Views are named saved configurations (table, Gantt, calendar, board) that wrap
a query. They are read-only from the v3 API — creation and modification happens
through the Phase C query tools and the web UI.
"""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read", "queries", "list_views"})
async def list_views() -> str:
    """List all saved views in OpenProject.

    Views are named configurations (table, Gantt, calendar, board) that
    wrap a saved query. Use this to discover view IDs for get_view.

    Returns:
        List of views with their IDs, names, and types
    """
    try:
        client = get_client()
        result = await client.get_views()
        views = result.get("_embedded", {}).get("elements", [])

        if not views:
            return "No views found."

        text = f"✅ **Views ({len(views)}):**\n\n"
        for v in views:
            vtype = v.get("_links", {}).get("viewType", {}).get("title", "Unknown")
            starred = " ⭐" if v.get("starred") else ""
            public = " (public)" if v.get("public") else ""
            text += f"- **{v.get('name', 'Unnamed')}**{starred}{public} (ID: {v.get('id', 'N/A')}, type: {vtype})\n"
        return text

    except Exception as e:
        return format_error(f"Failed to list views: {e!s}")


@mcp.tool(tags={"read", "queries", "get_view"})
async def get_view(view_id: int) -> str:
    """Get details of a specific view.

    Args:
        view_id: The view ID (from list_views)

    Returns:
        View name, type, and associated query details
    """
    try:
        client = get_client()
        v = await client.get_view(view_id)

        text = f"✅ **View #{v.get('id', view_id)}:**\n\n"
        text += f"**Name**: {v.get('name', 'N/A')}\n"
        vtype = v.get("_links", {}).get("viewType", {}).get("title")
        if vtype:
            text += f"**Type**: {vtype}\n"
        text += f"**Public**: {'Yes' if v.get('public') else 'No'}\n"
        text += f"**Starred**: {'Yes' if v.get('starred') else 'No'}\n"
        query = v.get("_links", {}).get("query", {}).get("title")
        if query:
            text += f"**Query**: {query}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get view #{view_id}: {e!s}")
