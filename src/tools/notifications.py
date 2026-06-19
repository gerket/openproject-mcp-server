"""Notification management tools for OpenProject."""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read", "notifications", "core", "core-read", "list_notifications"})
async def list_notifications(
    unread_only: bool = True,
    page_size: int = 20,
) -> str:
    """List notifications for the authenticated API user.

    Args:
        unread_only: If True, only return unread notifications (default: True)
        page_size: Number of results to return (default: 20, max: 100)

    Returns:
        Formatted list of notifications with subject, reason, and linked resource
    """
    try:
        import json

        client = get_client()

        filters = None
        if unread_only:
            filters = json.dumps([{"readIAN": {"operator": "=", "values": ["f"]}}])

        result = await client.get_notifications(filters=filters, page_size=page_size)
        items = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(items))

        if not items:
            return (
                "✅ No unread notifications." if unread_only else "✅ No notifications."
            )

        text = f"🔔 **Notifications** ({total} total):\n\n"
        for n in items:
            subject = n.get("subject", "No subject")
            reason = n.get("reason", "")
            created = n.get("createdAt", "")[:10]
            read = n.get("readIAN", True)

            status = "📬" if not read else "📭"
            text += f"{status} **{subject}**\n"
            if reason:
                text += f"  Reason: {reason}\n"
            if created:
                text += f"  Date: {created}\n"

            resource_link = n.get("_links", {}).get("resource", {})
            if resource_link.get("title"):
                text += f"  Resource: {resource_link['title']} ({resource_link.get('href', '')})\n"

            text += f"  ID: {n.get('id', 'N/A')}\n\n"

        return text
    except Exception as e:
        return format_error(f"Failed to list notifications: {e!s}")


@mcp.tool(tags={"write", "notifications", "mark_notification_read"})
async def mark_notification_read(notification_id: int) -> str:
    """Mark a single notification as read.

    Args:
        notification_id: The notification ID (from list_notifications)

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.mark_notification_read(notification_id)
        return f"✅ Notification #{notification_id} marked as read."
    except Exception as e:
        return format_error(f"Failed to mark notification read: {e!s}")


@mcp.tool(
    tags={"write", "notifications", "core", "core-write", "mark_all_notifications_read"}
)
async def mark_all_notifications_read() -> str:
    """Mark all notifications as read for the current API user.

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.mark_all_notifications_read()
        return "✅ All notifications marked as read."
    except Exception as e:
        return format_error(f"Failed to mark all notifications read: {e!s}")
