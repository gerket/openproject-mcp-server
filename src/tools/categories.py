"""Category tools (Phase G).

Categories are project-scoped labels that can be applied to work packages.
They are distinct from work package types. All endpoints are read-only in v3.
"""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read", "projects", "list_categories"})
async def list_categories(project_id: int) -> str:
    """List work package categories for a project.

    Categories are optional project-specific labels (e.g. "Backend", "Frontend")
    that can be applied to work packages. May be empty if the project doesn't use them.

    Args:
        project_id: The project ID

    Returns:
        List of categories for the project
    """
    try:
        client = get_client()
        result = await client.get_project_categories(project_id)
        categories = result.get("_embedded", {}).get("elements", [])

        if not categories:
            return (
                f"No categories defined for project #{project_id}. "
                "Create them at Project Settings → Work packages → Categories."
            )

        text = f"✅ **Categories for Project #{project_id} ({len(categories)}):**\n\n"
        for c in categories:
            text += f"- **{c.get('name', 'Unnamed')}** (ID: {c.get('id', 'N/A')})\n"
        return text

    except Exception as e:
        return format_error(
            f"Failed to list categories for project #{project_id}: {e!s}"
        )


@mcp.tool(tags={"read", "projects", "get_category"})
async def get_category(category_id: int) -> str:
    """Get details of a specific work package category.

    Args:
        category_id: The category ID

    Returns:
        Category name and project association
    """
    try:
        client = get_client()
        c = await client.get_category(category_id)

        text = f"✅ **Category #{c.get('id', category_id)}:**\n\n"
        text += f"**Name**: {c.get('name', 'N/A')}\n"
        project = c.get("_links", {}).get("project", {}).get("title")
        if project:
            text += f"**Project**: {project}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get category #{category_id}: {e!s}")
