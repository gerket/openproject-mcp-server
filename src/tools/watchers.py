"""Watcher, activity, and available-assignee tools for OpenProject work packages."""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read", "work-packages"})
async def list_watchers(work_package_id: int) -> str:
    """List all users watching a work package.

    Args:
        work_package_id: The work package ID

    Returns:
        List of watchers with IDs and names
    """
    try:
        client = get_client()
        result = await client.get_watchers(work_package_id)
        watchers = result.get("_embedded", {}).get("elements", [])
        if not watchers:
            return f"✅ No watchers on work package #{work_package_id}."
        text = f"✅ **Watchers on WP #{work_package_id}** ({len(watchers)}):\n\n"
        for w in watchers:
            text += f"- **{w.get('name', 'Unknown')}** (ID: {w.get('id', 'N/A')})\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list watchers: {e!s}")


@mcp.tool(tags={"read", "work-packages"})
async def list_available_watchers(work_package_id: int) -> str:
    """List users eligible to watch a work package (project members with view access).

    Useful for autocomplete when adding a watcher.

    Args:
        work_package_id: The work package ID

    Returns:
        List of eligible watchers with IDs and names
    """
    try:
        client = get_client()
        result = await client.get_available_watchers(work_package_id)
        users = result.get("_embedded", {}).get("elements", [])
        if not users:
            return "✅ No users available to watch this work package."
        text = f"✅ **Available watchers** ({len(users)}):\n\n"
        for u in users:
            text += f"- **{u.get('name', 'Unknown')}** (ID: {u.get('id', 'N/A')})\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list available watchers: {e!s}")


@mcp.tool(tags={"write", "work-packages"})
async def add_watcher(work_package_id: int, user_id: int) -> str:
    """Add a user as a watcher on a work package.

    Args:
        work_package_id: The work package ID
        user_id: The user ID to add as watcher (use list_available_watchers to find IDs)

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.add_watcher(work_package_id, user_id)
        return f"✅ User #{user_id} is now watching work package #{work_package_id}."
    except Exception as e:
        return format_error(f"Failed to add watcher: {e!s}")


@mcp.tool(tags={"write", "work-packages"})
async def remove_watcher(work_package_id: int, user_id: int) -> str:
    """Remove a user from the watcher list of a work package.

    Args:
        work_package_id: The work package ID
        user_id: The user ID to remove (use list_watchers to find IDs)

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.remove_watcher(work_package_id, user_id)
        return f"✅ User #{user_id} removed from watchers of work package #{work_package_id}."
    except Exception as e:
        return format_error(f"Failed to remove watcher: {e!s}")


@mcp.tool(tags={"read", "work-packages"})
async def get_activity(activity_id: int) -> str:
    """Get a single activity (comment or field change) by ID.

    Activity IDs appear in list_work_package_activities output.

    Args:
        activity_id: The activity ID

    Returns:
        Activity details including comment text and author
    """
    try:
        client = get_client()
        activity = await client.get_activity(activity_id)
        text = f"✅ **Activity #{activity.get('id')}**\n\n"
        links = activity.get("_links", {})
        author = links.get("user", {}).get("title") or links.get("author", {}).get(
            "title", "Unknown"
        )
        text += f"**Author**: {author}\n"
        if activity.get("createdAt"):
            text += f"**Date**: {activity['createdAt'][:10]}\n"
        if activity.get("internal"):
            text += "**Internal**: Yes\n"
        comment = activity.get("comment", {})
        if isinstance(comment, dict) and comment.get("raw"):
            text += f"\n{comment['raw']}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get activity: {e!s}")


@mcp.tool(tags={"write", "work-packages"})
async def update_activity(
    activity_id: int,
    comment: str,
    internal: bool = False,
) -> str:
    """Edit the comment on a work package activity.

    Requires the 'edit journals' permission on the project.

    Args:
        activity_id: The activity ID to edit (from list_work_package_activities)
        comment: New comment text (Markdown supported)
        internal: If True, mark as internal (team-only). Default: False

    Returns:
        Success message with updated comment preview
    """
    try:
        client = get_client()
        activity = await client.update_activity(activity_id, comment, internal=internal)
        updated_raw = activity.get("comment", {}).get("raw", comment)
        text = f"✅ Activity #{activity_id} updated.\n\n"
        text += f"**Comment**: {updated_raw[:200]}{'...' if len(updated_raw) > 200 else ''}\n"
        if internal:
            text += "**Internal**: Yes\n"
        return text
    except Exception as e:
        return format_error(f"Failed to update activity: {e!s}")


@mcp.tool(tags={"read", "work-packages"})
async def list_available_assignees(work_package_id: int) -> str:
    """List users eligible to be assigned to a work package.

    More useful than list_users for assignment because it is scoped to project
    members who have the 'Work package assignee' role on this specific WP's project.

    Args:
        work_package_id: The work package ID

    Returns:
        List of assignable users with IDs and names
    """
    try:
        client = get_client()
        result = await client.get_available_assignees(work_package_id)
        users = result.get("_embedded", {}).get("elements", [])
        if not users:
            return "✅ No users available to assign to this work package."
        text = f"✅ **Available assignees** ({len(users)}):\n\n"
        for u in users:
            text += f"- **{u.get('name', 'Unknown')}** (ID: {u.get('id', 'N/A')})\n"
            if u.get("email"):
                text += f"  Email: {u['email']}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list available assignees: {e!s}")
