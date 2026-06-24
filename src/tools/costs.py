"""Budget tools for OpenProject.

The v3 API exposes budgets read-only:
  GET /projects/{id}/budgets — list budgets for a project
  GET /budgets/{id}          — get a single budget

Cost types and cost entry management (create/read/update/delete) are not part
of the core OpenProject v3 API spec and are not implemented here.
"""

from src.server import get_client
from src.tool_registry import tracked_tool
from src.utils.formatting import format_error


@tracked_tool(tags={"read", "budgets", "budgets-read", "list_budgets"})
async def list_budgets(project_id: int) -> str:
    """List budgets for a project.

    Args:
        project_id: The project ID

    Returns:
        List of budgets with their details, or a message if none exist
    """
    try:
        client = get_client()
        result = await client._request("GET", f"/projects/{project_id}/budgets")
        budgets = result.get("_embedded", {}).get("elements", [])

        if not budgets:
            return f"No budgets found for project #{project_id}."

        text = f"✅ **Budgets for Project #{project_id} ({len(budgets)}):**\n\n"
        for b in budgets:
            text += f"**{b.get('subject', 'Unnamed')}** (ID: {b.get('id', 'N/A')})\n"
            if b.get("description", {}).get("raw"):
                text += f"  Description: {b['description']['raw']}\n"
            text += "\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list budgets: {e!s}")


@tracked_tool(tags={"read", "budgets", "budgets-read", "get_budget"})
async def get_budget(budget_id: int) -> str:
    """Get a budget by ID.

    Args:
        budget_id: The budget ID

    Returns:
        Budget details
    """
    try:
        client = get_client()
        b = await client._request("GET", f"/budgets/{budget_id}")

        text = f"✅ **Budget #{b.get('id', budget_id)}:**\n\n"
        text += f"**Subject**: {b.get('subject', 'N/A')}\n"
        if b.get("description", {}).get("raw"):
            text += f"**Description**: {b['description']['raw']}\n"
        project = b.get("_links", {}).get("project", {}).get("title")
        if project:
            text += f"**Project**: {project}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get budget #{budget_id}: {e!s}")
