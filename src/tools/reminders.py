"""Reminder tools for OpenProject work packages."""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read"})
async def list_reminders(work_package_id: int) -> str:
    """List reminders set on a work package for the current API user.

    Args:
        work_package_id: The work package ID

    Returns:
        List of reminders with dates, notes, and completion status
    """
    try:
        client = get_client()
        result = await client.get_reminders(work_package_id)
        reminders = result.get("_embedded", {}).get("elements", [])
        if not reminders:
            return f"✅ No reminders on work package #{work_package_id}."
        text = f"✅ **Reminders on WP #{work_package_id}** ({len(reminders)}):\n\n"
        for r in reminders:
            remind_at = r.get("remindAt", "")[:16].replace("T", " ")
            completed = r.get("completed", False)
            status = "✅" if completed else "⏰"
            text += f"{status} **{remind_at}**"
            if r.get("note"):
                text += f" — {r['note']}"
            text += f" (ID: {r.get('id', 'N/A')})\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list reminders: {e!s}")


@mcp.tool(tags={"write"})
async def create_reminder(
    work_package_id: int,
    remind_at: str,
    note: str | None = None,
) -> str:
    """Create a reminder on a work package for the current API user.

    Args:
        work_package_id: The work package ID
        remind_at: ISO 8601 datetime when to remind (e.g. '2026-06-25T09:00:00Z')
        note: Optional reminder note

    Returns:
        Success message with reminder ID and scheduled time

    Example:
        {
            "work_package_id": 42,
            "remind_at": "2026-06-25T09:00:00Z",
            "note": "Review acceptance criteria"
        }
    """
    try:
        client = get_client()
        reminder = await client.create_reminder(work_package_id, remind_at, note=note)
        reminder_id = reminder.get("id", "N/A")
        remind_str = reminder.get("remindAt", remind_at)[:16].replace("T", " ")
        text = f"✅ Reminder #{reminder_id} created for WP #{work_package_id}.\n\n"
        text += f"**Remind at**: {remind_str}\n"
        if note:
            text += f"**Note**: {note}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to create reminder: {e!s}")
