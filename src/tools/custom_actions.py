"""Custom actions tools — workflow buttons defined by OpenProject admins."""

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_success


@mcp.tool(tags={"read", "work_packages", "list_custom_actions"})
async def list_custom_actions() -> str:
    """List all custom actions available in the OpenProject instance.

    Custom actions are admin-defined workflow buttons that trigger status
    transitions or field updates on work packages. Use this to discover
    available action IDs before calling execute_custom_action.

    Returns:
        List of custom actions with their IDs and names
    """
    try:
        client = get_client()
        result = await client.list_custom_actions()
        actions = result.get("_embedded", {}).get("elements", [])

        if not actions:
            return "No custom actions found. Create them in Administration → Work packages → Custom actions."

        text = f"✅ **Custom Actions ({len(actions)}):**\n\n"
        for action in actions:
            text += (
                f"**{action.get('name', 'Unnamed')}** (ID: {action.get('id', 'N/A')})\n"
            )
            if action.get("description", {}).get("raw"):
                text += f"  Description: {action['description']['raw']}\n"
            text += "\n"
        return text

    except Exception as e:
        err = str(e)
        if "404" in err:
            return (
                "⚠️ The `GET /custom_actions` collection endpoint is not available on this "
                "OpenProject instance (Community Edition returns 404 for this endpoint). "
                "Use `get_custom_action(action_id)` with a known ID instead, or check "
                "Administration → Work packages → Custom actions in the web UI to find IDs."
            )
        return format_error(f"Failed to list custom actions: {err}")


@mcp.tool(tags={"read", "work_packages", "get_custom_action"})
async def get_custom_action(action_id: int) -> str:
    """Get details of a specific custom action by ID.

    Args:
        action_id: The custom action ID

    Returns:
        Custom action details including name, description, and conditions
    """
    try:
        client = get_client()
        action = await client.get_custom_action(action_id)

        # The API response has no top-level "id" — use the supplied action_id.
        text = f"✅ **Custom Action #{action_id}:**\n\n"
        text += f"**Name**: {action.get('name', 'N/A')}\n"
        if action.get("description", {}).get("raw"):
            text += f"**Description**: {action['description']['raw']}\n"

        conditions = action.get("_embedded", {}).get("conditions", [])
        if conditions:
            text += f"**Conditions**: {len(conditions)} defined\n"

        actions_list = action.get("_embedded", {}).get("actions", [])
        if actions_list:
            text += "**Actions**:\n"
            for a in actions_list:
                text += f"  - {a.get('_type', 'unknown')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get custom action #{action_id}: {e!s}")


@mcp.tool(tags={"write", "work_packages", "execute_custom_action"})
async def execute_custom_action(action_id: int, work_package_id: int) -> str:
    """Execute a custom action against a work package.

    Custom actions are admin-defined workflow buttons (e.g. "Start Progress",
    "Ready for Review") that trigger status transitions or field updates.
    The current lockVersion is fetched automatically before execution.

    Args:
        action_id: The custom action ID (use list_custom_actions to discover IDs)
        work_package_id: The work package to apply the action to

    Returns:
        Success message with the updated work package details, or an error if
        the action is not applicable to the work package's current state
    """
    try:
        client = get_client()
        result = await client.execute_custom_action(action_id, work_package_id)

        wp = result.get("_embedded", {}).get("workPackage", result)
        text = format_success(
            f"Custom action #{action_id} executed on work package #{work_package_id}.\n\n"
        )
        text += f"**Work Package**: #{wp.get('id', work_package_id)} — {wp.get('subject', 'N/A')}\n"
        status_href = wp.get("_links", {}).get("status", {}).get("title", "")
        if status_href:
            text += f"**Status**: {status_href}\n"
        return text

    except Exception as e:
        return format_error(
            f"Failed to execute custom action #{action_id} on work package #{work_package_id}: {e!s}"
        )
