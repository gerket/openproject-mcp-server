"""Cost type and cost entry tools for OpenProject."""

from typing import Any

from pydantic import BaseModel, Field

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_success


class CreateCostEntryInput(BaseModel):
    project_id: int = Field(..., description="Project ID", gt=0)
    work_package_id: int = Field(
        ..., description="Work package ID to log cost against", gt=0
    )
    cost_type_id: int = Field(
        ..., description="Cost type ID (from list_cost_types)", gt=0
    )
    units: float = Field(..., description="Quantity of units (e.g. token count)", ge=0)
    spent_on: str = Field(..., description="Date the cost was incurred (YYYY-MM-DD)")
    comment: str | None = Field(None, description="Optional comment/note")


class UpdateCostEntryInput(BaseModel):
    cost_entry_id: int = Field(..., description="Cost entry ID to update", gt=0)
    units: float | None = Field(None, description="New unit quantity", ge=0)
    spent_on: str | None = Field(None, description="New date (YYYY-MM-DD)")
    comment: str | None = Field(None, description="New comment")


@mcp.tool(tags={"read", "finance", "all"})
async def list_cost_types() -> str:
    """List all defined cost types in the OpenProject instance.

    Use this to find the ID for cost types like 'Claude Sonnet Input Tokens'
    before logging cost entries.

    Returns:
        List of cost types with IDs, names, units, and rates
    """
    try:
        client = get_client()
        result = await client.get_cost_types()
        types = result.get("_embedded", {}).get("elements", [])

        if not types:
            return (
                "No cost types found. The Costs module may not be enabled on this instance, "
                "or no cost types have been defined yet (requires admin setup)."
            )

        text = f"✅ **Cost Types ({len(types)}):**\n\n"
        for ct in types:
            text += f"- **{ct.get('name', 'Unnamed')}** (ID: {ct.get('id', 'N/A')})\n"
            if ct.get("unit"):
                text += f"  Unit: {ct['unit']}\n"
            if ct.get("rate") is not None:
                text += f"  Default rate: {ct['rate']}\n"
            if not ct.get("isDefault", True):
                text += "  (custom type)\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list cost types: {e!s}")


@mcp.tool(tags={"read", "finance", "all"})
async def list_cost_entries(
    work_package_id: int | None = None,
    project_id: int | None = None,
) -> str:
    """List cost entries, optionally filtered by work package or project.

    Args:
        work_package_id: Filter to entries logged against this work package
        project_id: Filter to entries in this project

    Returns:
        List of cost entries with type, units, date, and comment
    """
    try:
        client = get_client()
        result = await client.get_cost_entries(
            work_package_id=work_package_id, project_id=project_id
        )
        entries = result.get("_embedded", {}).get("elements", [])

        if not entries:
            return "No cost entries found."

        text = f"✅ **Cost Entries ({len(entries)}):**\n\n"
        for e in entries:
            links = e.get("_links", {})
            ct_name = links.get("costType", {}).get("title", "Unknown type")
            wp_title = links.get("workPackage", {}).get("title", "")
            text += (
                f"- **ID {e.get('id', 'N/A')}**: {e.get('units', '?')} x {ct_name}\n"
            )
            text += f"  Date: {e.get('spentOn', 'N/A')}\n"
            if wp_title:
                text += f"  Work package: {wp_title}\n"
            comment = e.get("comment", {})
            if isinstance(comment, dict) and comment.get("raw"):
                text += f"  Comment: {comment['raw'][:80]}\n"
            text += "\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list cost entries: {e!s}")


@mcp.tool(tags={"write", "finance", "all"})
async def create_cost_entry(input: CreateCostEntryInput) -> str:
    """Log a cost entry against a work package.

    Common use: log AI token consumption after a Claude session.
    Use list_cost_types first to find the correct cost_type_id.

    Args:
        input: Cost entry data including project_id, work_package_id,
               cost_type_id, units (token count), spent_on date, and optional comment

    Returns:
        Success message with the created entry ID

    Example — log Claude Sonnet input tokens:
        {
            "project_id": 3,
            "work_package_id": 42,
            "cost_type_id": 1,
            "units": 47382,
            "spent_on": "2026-06-17",
            "comment": "Claude session: phase plan research"
        }
    """
    try:
        client = get_client()
        entry = await client.create_cost_entry(
            {
                "project_id": input.project_id,
                "work_package_id": input.work_package_id,
                "cost_type_id": input.cost_type_id,
                "units": input.units,
                "spent_on": input.spent_on,
                "comment": input.comment,
            }
        )
        entry_id = entry.get("id", "N/A")
        result = format_success(f"Cost entry #{entry_id} created.")
        result += f"\n\n**Units**: {entry.get('units', input.units)}"
        result += f"\n**Date**: {entry.get('spentOn', input.spent_on)}"
        links = entry.get("_links", {})
        ct = links.get("costType", {}).get("title")
        if ct:
            result += f"\n**Cost type**: {ct}"
        return result
    except Exception as e:
        return format_error(f"Failed to create cost entry: {e!s}")


@mcp.tool(tags={"write", "finance", "all"})
async def update_cost_entry(input: UpdateCostEntryInput) -> str:
    """Update an existing cost entry (units, date, or comment).

    Args:
        input: Update data including cost_entry_id and fields to change

    Returns:
        Success message with updated entry details
    """
    try:
        data: dict[str, Any] = {}
        if input.units is not None:
            data["units"] = input.units
        if input.spent_on is not None:
            data["spent_on"] = input.spent_on
        if input.comment is not None:
            data["comment"] = input.comment
        if not data:
            return format_error("No fields provided to update.")

        client = get_client()
        entry = await client.update_cost_entry(input.cost_entry_id, data)
        result = format_success(f"Cost entry #{input.cost_entry_id} updated.")
        result += f"\n\n**Units**: {entry.get('units', '?')}"
        result += f"\n**Date**: {entry.get('spentOn', '?')}"
        return result
    except Exception as e:
        return format_error(f"Failed to update cost entry: {e!s}")


@mcp.tool(tags={"write", "finance", "all"})
async def delete_cost_entry(cost_entry_id: int) -> str:
    """Delete a cost entry permanently.

    WARNING: Cannot be undone.

    Args:
        cost_entry_id: The cost entry ID to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_cost_entry(cost_entry_id)
        return format_success(f"Cost entry #{cost_entry_id} deleted.")
    except Exception as e:
        return format_error(f"Failed to delete cost entry: {e!s}")
