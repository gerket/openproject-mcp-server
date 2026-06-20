"""Placeholder user management tools.

Placeholder users are non-login stub identities (e.g. "External Consultant",
"Design Team") that can be assigned to work packages and added to projects
but cannot authenticate. They have no email or login — only a name.
"""

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_success


@mcp.tool(tags={"read", "users", "list_placeholder_users"})
async def list_placeholder_users() -> str:
    """List all placeholder users in the OpenProject instance.

    Placeholder users are non-login stub identities used for assignment
    when the real person is not a system user.

    Returns:
        List of placeholder users with their IDs and names
    """
    try:
        client = get_client()
        result = await client.get_placeholder_users()
        users = result.get("_embedded", {}).get("elements", [])

        if not users:
            return "No placeholder users found."

        text = f"✅ **Placeholder Users ({len(users)}):**\n\n"
        for u in users:
            text += f"- **{u.get('name', 'Unnamed')}** (ID: {u.get('id', 'N/A')})\n"
        return text

    except Exception as e:
        return format_error(f"Failed to list placeholder users: {e!s}")


@mcp.tool(tags={"read", "users", "get_placeholder_user"})
async def get_placeholder_user(placeholder_id: int) -> str:
    """Get details of a specific placeholder user.

    Args:
        placeholder_id: The placeholder user ID

    Returns:
        Placeholder user details
    """
    try:
        client = get_client()
        u = await client.get_placeholder_user(placeholder_id)

        text = f"✅ **Placeholder User #{u.get('id', placeholder_id)}:**\n\n"
        text += f"**Name**: {u.get('name', 'N/A')}\n"
        if u.get("createdAt"):
            text += f"**Created**: {u['createdAt']}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get placeholder user #{placeholder_id}: {e!s}")


@mcp.tool(tags={"write", "users", "create_placeholder_user"})
async def create_placeholder_user(name: str) -> str:
    """Create a placeholder user.

    Placeholder users are non-login stubs used for work package assignment
    when the real person is not a system user. Only a name is required.

    Args:
        name: Display name for the placeholder (e.g. "External Consultant")

    Returns:
        Success message with the new placeholder user ID
    """
    try:
        client = get_client()
        u = await client.create_placeholder_user(name)
        text = format_success("Placeholder user created.\n\n")
        text += f"**ID**: #{u.get('id', 'N/A')}\n"
        text += f"**Name**: {u.get('name', 'N/A')}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to create placeholder user: {e!s}")


@mcp.tool(tags={"write", "users", "update_placeholder_user"})
async def update_placeholder_user(placeholder_id: int, name: str) -> str:
    """Update a placeholder user's name.

    Args:
        placeholder_id: The placeholder user ID to update
        name: New display name

    Returns:
        Success message with the updated name
    """
    try:
        client = get_client()
        u = await client.update_placeholder_user(placeholder_id, name)
        text = format_success(f"Placeholder user #{placeholder_id} updated.\n\n")
        text += f"**Name**: {u.get('name', 'N/A')}\n"
        return text

    except Exception as e:
        return format_error(
            f"Failed to update placeholder user #{placeholder_id}: {e!s}"
        )


@mcp.tool(tags={"write", "users", "admin", "delete_placeholder_user"})
async def delete_placeholder_user(placeholder_id: int) -> str:
    """Delete a placeholder user permanently (admin only).

    Args:
        placeholder_id: The placeholder user ID to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_placeholder_user(placeholder_id)
        return format_success(f"Placeholder user #{placeholder_id} deleted.")

    except Exception as e:
        if "403" in str(e):
            return format_error(
                "delete_placeholder_user requires administrator privileges."
            )
        return format_error(
            f"Failed to delete placeholder user #{placeholder_id}: {e!s}"
        )
