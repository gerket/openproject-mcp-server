"""Query (saved view) management tools for OpenProject."""

from typing import Any

from src.server import get_client
from src.tool_registry import tracked_tool
from src.utils.formatting import format_error


def _build_query_links(
    column_names: list[str] | None = None,
    sort_by: str | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    """Build the HAL _links dict for a query payload."""
    links: dict[str, Any] = {}
    if project_id is not None:
        links["project"] = {"href": f"/api/v3/projects/{project_id}"}
    if column_names:
        links["columns"] = [
            {"href": f"/api/v3/queries/columns/{col}"} for col in column_names
        ]
    if sort_by:
        links["sortBy"] = [{"href": f"/api/v3/queries/sort_bys/{sort_by}"}]
    return links


def _build_query_payload(
    name: str,
    project_id: int | None = None,
    column_names: list[str] | None = None,
    sort_by: str | None = None,
    public: bool = False,
) -> dict[str, Any]:
    """Build a full HAL query payload for create.

    Args:
        name: Query name
        project_id: Optional project to scope the query to
        column_names: Column identifiers in display order
            (e.g. ["id", "subject", "status", "assignee", "dueDate"])
        sort_by: Sort spec in '{column}-{asc|desc}' format
            (e.g. "updatedAt-desc", "dueDate-asc")
        public: Whether the query is visible to all project members
    """
    return {
        "name": name,
        "public": public,
        "_links": _build_query_links(
            column_names=column_names, sort_by=sort_by, project_id=project_id
        ),
    }


@tracked_tool(tags={"read", "queries", "core", "core-read", "list_queries"})
async def list_queries(
    project_id: int | None = None,
) -> str:
    """List saved queries (work-package views).

    Args:
        project_id: Optional project ID to scope the listing

    Returns:
        List of queries with IDs, names, and public/private status
    """
    try:
        client = get_client()
        result = await client.get_queries(project_id=project_id)
        queries = result.get("_embedded", {}).get("elements", [])
        if not queries:
            return "✅ No queries found."
        text = f"✅ **Saved queries** ({len(queries)}):\n\n"
        for q in queries:
            public = "🌐 public" if q.get("public") else "🔒 private"
            starred = " ⭐" if q.get("starred") else ""
            text += f"- **{q.get('name', 'Unnamed')}** (ID: {q.get('id', 'N/A')}) — {public}{starred}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list queries: {e!s}")


@tracked_tool(tags={"read", "queries", "core", "core-read", "get_query"})
async def get_query(query_id: int) -> str:
    """Get a saved query by ID, including its filters, columns, and sort order.

    Args:
        query_id: The query ID (from list_queries)

    Returns:
        Query details including name, filters, columns, and sort order
    """
    try:
        client = get_client()
        q = await client.get_query(query_id)
        text = f"✅ **Query #{q.get('id')}: {q.get('name', 'Unnamed')}**\n\n"
        text += f"**Public**: {'Yes' if q.get('public') else 'No'}\n"
        text += f"**Starred**: {'Yes' if q.get('starred') else 'No'}\n"
        links = q.get("_links", {})
        if links.get("project", {}).get("title"):
            text += f"**Project**: {links['project']['title']}\n"
        columns = links.get("columns", [])
        if columns:
            col_names = [
                c.get("title") or c.get("href", "").split("/")[-1] for c in columns
            ]
            text += f"**Columns**: {', '.join(col_names)}\n"
        sort_by = links.get("sortBy", [])
        if sort_by:
            sorts = [
                s.get("title") or s.get("href", "").split("/")[-1] for s in sort_by
            ]
            text += f"**Sort by**: {', '.join(sorts)}\n"
        filters = q.get("filters", [])
        if filters:
            text += f"**Filters** ({len(filters)}):\n"
            for f in filters:
                f_links = f.get("_links", {})
                fname = (
                    f_links.get("filter", {}).get("title")
                    or f_links.get("filter", {}).get("href", "").split("/")[-1]
                )
                op = (
                    f_links.get("operator", {}).get("title")
                    or f_links.get("operator", {}).get("href", "").split("/")[-1]
                )
                text += f"  - {fname}: {op}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get query: {e!s}")


@tracked_tool(tags={"read", "queries", "get_default_query"})
async def get_default_query(project_id: int | None = None) -> str:
    """Get the default query configuration.

    Args:
        project_id: Optional project ID for a project-scoped default

    Returns:
        Default query details
    """
    try:
        client = get_client()
        q = await client.get_default_query(project_id=project_id)
        text = f"✅ **Default query: {q.get('name', 'Default')}**\n\n"
        links = q.get("_links", {})
        columns = links.get("columns", [])
        if columns:
            col_names = [
                c.get("title") or c.get("href", "").split("/")[-1] for c in columns
            ]
            text += f"**Columns**: {', '.join(col_names)}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get default query: {e!s}")


@tracked_tool(tags={"write", "queries", "core", "core-write", "create_query"})
async def create_query(
    name: str,
    project_id: int | None = None,
    column_names: list[str] | None = None,
    sort_by: str | None = None,
    public: bool = False,
) -> str:
    """Create a saved query (work-package view).

    Args:
        name: Query name (required)
        project_id: Optional project ID to scope this query
        column_names: Columns to show in order. Valid names:
            id, subject, type, status, assignee, priority,
            dueDate, startDate, percentageDone, updatedAt, createdAt, author
        sort_by: Sort in '{column}-{asc|desc}' format (e.g. 'updatedAt-desc')
        public: If True, visible to all project members (default: False)

    Returns:
        Success message with query ID

    Example:
        {
            "name": "Open bugs by due date",
            "project_id": 4,
            "column_names": ["id", "subject", "status", "assignee", "dueDate"],
            "sort_by": "dueDate-asc",
            "public": false
        }
    """
    try:
        client = get_client()
        payload = _build_query_payload(
            name=name,
            project_id=project_id,
            column_names=column_names,
            sort_by=sort_by,
            public=public,
        )
        q = await client.create_query(payload)
        query_id = q.get("id", "N/A")
        text = f"✅ Query #{query_id} '{q.get('name', name)}' created.\n\n"
        text += f"**Public**: {'Yes' if public else 'No'}\n"
        if project_id:
            text += f"**Project ID**: {project_id}\n"
        if column_names:
            text += f"**Columns**: {', '.join(column_names)}\n"
        if sort_by:
            text += f"**Sort**: {sort_by}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to create query: {e!s}")


@tracked_tool(tags={"write", "queries", "update_query"})
async def update_query(
    query_id: int,
    name: str | None = None,
    column_names: list[str] | None = None,
    sort_by: str | None = None,
    public: bool | None = None,
) -> str:
    """Update a saved query.

    Only supply the fields you want to change.

    Args:
        query_id: The query ID to update
        name: New query name
        column_names: New column list (replaces existing columns)
        sort_by: New sort spec (e.g. 'dueDate-asc')
        public: Change public/private status

    Returns:
        Success message with updated query name
    """
    try:
        client = get_client()
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if public is not None:
            data["public"] = public
        links = _build_query_links(column_names=column_names, sort_by=sort_by)
        if links:
            data["_links"] = links
        if not data:
            return format_error("No fields provided to update.")
        q = await client.update_query(query_id, data)
        return f"✅ Query #{query_id} updated: '{q.get('name', query_id)}'\n"
    except Exception as e:
        return format_error(f"Failed to update query: {e!s}")


@tracked_tool(tags={"write", "queries", "delete_query"})
async def delete_query(query_id: int) -> str:
    """Delete a saved query permanently.

    WARNING: Cannot be undone.

    Args:
        query_id: The query ID to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_query(query_id)
        return f"✅ Query #{query_id} deleted."
    except Exception as e:
        return format_error(f"Failed to delete query: {e!s}")


@tracked_tool(tags={"write", "queries", "star_query"})
async def star_query(query_id: int) -> str:
    """Star a query to pin it at the top of the query list.

    Args:
        query_id: The query ID to star

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.star_query(query_id)
        return f"✅ Query #{query_id} starred."
    except Exception as e:
        return format_error(f"Failed to star query: {e!s}")


@tracked_tool(tags={"write", "queries", "unstar_query"})
async def unstar_query(query_id: int) -> str:
    """Unstar a query.

    Args:
        query_id: The query ID to unstar

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.unstar_query(query_id)
        return f"✅ Query #{query_id} unstarred."
    except Exception as e:
        return format_error(f"Failed to unstar query: {e!s}")
