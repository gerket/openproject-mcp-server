"""Group management tools for OpenProject (read-only)."""

from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


@mcp.tool
async def list_groups() -> str:
    """List all groups in the OpenProject instance.

    Returns:
        List of groups with IDs and names
    """
    try:
        client = get_client()
        result = await client.get_groups()
        groups = result.get("_embedded", {}).get("elements", [])

        if not groups:
            return "No groups found."

        text = f"✅ **Found {len(groups)} group(s):**\n\n"
        for group in groups:
            text += f"- **{group.get('name', 'Unnamed')}** (ID: {group.get('id', 'N/A')})\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list groups: {str(e)}")


@mcp.tool
async def get_group(group_id: int) -> str:
    """Get detailed information about a specific group.

    Args:
        group_id: The group ID

    Returns:
        Group details including name and metadata
    """
    try:
        client = get_client()
        group = await client.get_group(group_id)

        text = f"✅ **Group #{group.get('id')}**\n\n"
        text += f"**Name**: {group.get('name', 'Unknown')}\n"
        if group.get("updatedAt"):
            text += f"**Updated**: {group['updatedAt'][:10]}\n"

        members = group.get("_embedded", {}).get("members", [])
        if members:
            text += f"\n**Members** ({len(members)}):\n"
            for m in members:
                text += f"- {m.get('name', 'Unknown')} (ID: {m.get('id', 'N/A')})\n"

        return text
    except Exception as e:
        return format_error(f"Failed to get group: {str(e)}")
