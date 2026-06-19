# Phase C: Queries (Saved Views) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 8 query management tools so agents can save, load, star, and manage work-package view configurations — enabling persistent filter/sort/column layouts across sessions.

**Architecture:** One new client section in `src/client.py` (8 methods), one new tool module `src/tools/queries.py` (8 tools), registered in `src/server.py`. The hard part is HAL payload construction: the tool layer accepts plain strings for columns/sort-by and dicts for filters, then builds the nested `_links` structure the API expects. A `_build_query_payload` helper in the tool module owns this translation so the tool functions stay thin.

**Tech Stack:** Python 3.10+, FastMCP, Pydantic v2, pytest-asyncio

## Global Constraints

- Worktree: `/Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/phase-c-queries`
- Every `@mcp.tool` carries two tags: one access (`{"read"}` or `{"write"}`) + one category (`{"queries"}`)
- All client methods `async def`, return `dict` or `bool`
- All tools return `str`, catch all exceptions, use `format_error(...)`
- Tests: `async def test_*`, `.fn(...)` for decorated tools, `conftest.py` sets env vars
- Run with: `uv run pytest <file> -v`
- All source must pass: `uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501` and `uv run mypy src/ --ignore-missing-imports`
- Conventional commit messages; one commit per task

## HAL payload reference

The query API uses HAL `_links` for everything structural:

```json
{
  "name": "My open bugs",
  "public": false,
  "_links": {
    "project":  {"href": "/api/v3/projects/4"},
    "columns":  [{"href": "/api/v3/queries/columns/id"}, {"href": "/api/v3/queries/columns/subject"}],
    "sortBy":   [{"href": "/api/v3/queries/sort_bys/updatedAt-desc"}],
    "groupBy":  null
  },
  "filters": [
    {
      "_type": "StatusQueryFilter",
      "_links": {
        "filter":   {"href": "/api/v3/queries/filters/status"},
        "operator": {"href": "/api/v3/queries/operators/o"},
        "values":   []
      }
    }
  ]
}
```

**Column hrefs:** `/api/v3/queries/columns/{name}` — names: `id`, `subject`, `type`, `status`, `assignee`, `priority`, `dueDate`, `startDate`, `percentageDone`, `updatedAt`, `createdAt`, `author`

**Sort hrefs:** `/api/v3/queries/sort_bys/{column}-{asc|desc}`

**Filter structure:** Each filter has `_type` (e.g. `StatusQueryFilter`), `_links.filter` href, `_links.operator` href. Primitive values (status operator `o` = open, `*` = all) use `_links.values: []`. Non-primitive (user IDs, project IDs) use `_links.values: [{"href": "/api/v3/users/5"}]`.

## New tools summary

| Tool | Tags | Endpoint |
|---|---|---|
| `list_queries` | read, queries | `GET /queries` — optional `project_id` filter |
| `get_query` | read, queries | `GET /queries/{id}` |
| `get_default_query` | read, queries | `GET /queries/default` |
| `create_query` | write, queries | `POST /queries` |
| `update_query` | write, queries | `PATCH /queries/{id}` |
| `delete_query` | write, queries | `DELETE /queries/{id}` |
| `star_query` | write, queries | `PATCH /queries/{id}/star` |
| `unstar_query` | write, queries | `PATCH /queries/{id}/unstar` |

## File map

| File | Action |
|---|---|
| `src/client.py` | Append 8 client methods after `delete_cost_entry` section |
| `src/tools/queries.py` | Create — 8 tools + `_build_query_payload` helper |
| `src/server.py` | Add `queries` import; counts auto-update |
| `test_client_queries.py` | Unit tests for client methods |
| `test_queries.py` | Unit tests for tools |

---

### Task 1: Client methods

**Files:**
- Modify: `src/client.py` (append after `delete_cost_entry`)
- Create: `test_client_queries.py`

**Interfaces:**
- Produces:
  - `async def get_queries(self, project_id: int | None = None) -> dict`
  - `async def get_query(self, query_id: int) -> dict`
  - `async def get_default_query(self, project_id: int | None = None) -> dict`
  - `async def create_query(self, data: dict) -> dict`
  - `async def update_query(self, query_id: int, data: dict) -> dict`
  - `async def delete_query(self, query_id: int) -> bool`
  - `async def star_query(self, query_id: int) -> dict`
  - `async def unstar_query(self, query_id: int) -> dict`

- [ ] **Step 1: Write the failing test**

Create `test_client_queries.py`:

```python
"""Unit tests for query client methods (network-free)."""

import pytest

from src.client import OpenProjectClient
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client() -> OpenProjectClient:
    return OpenProjectClient(base_url="https://op.test", api_key="k")


@pytest.mark.asyncio
async def test_get_queries_no_project(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_queries()
        req.assert_called_once_with("GET", "/queries")


@pytest.mark.asyncio
async def test_get_queries_with_project(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_queries(project_id=4)
        call_endpoint = req.call_args[0][1]
        assert "project_id" in call_endpoint or "filters" in call_endpoint


@pytest.mark.asyncio
async def test_get_query(client):
    mock = {"id": 7, "name": "My query"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.get_query(7)
        req.assert_called_once_with("GET", "/queries/7")
        assert result == mock


@pytest.mark.asyncio
async def test_get_default_query(client):
    mock = {"id": 1, "name": "Default"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_default_query()
        req.assert_called_once_with("GET", "/queries/default")


@pytest.mark.asyncio
async def test_get_default_query_project(client):
    mock = {"id": 2, "name": "Default (project)"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_default_query(project_id=4)
        req.assert_called_once_with("GET", "/projects/4/queries/default")


@pytest.mark.asyncio
async def test_create_query(client):
    payload = {"name": "Test", "_links": {}}
    mock = {"id": 9, "name": "Test"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.create_query(payload)
        req.assert_called_once_with("POST", "/queries", payload)
        assert result == mock


@pytest.mark.asyncio
async def test_update_query(client):
    payload = {"name": "Updated"}
    mock = {"id": 9, "name": "Updated"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.update_query(9, payload)
        req.assert_called_once_with("PATCH", "/queries/9", payload)
        assert result == mock


@pytest.mark.asyncio
async def test_delete_query(client):
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as req:
        result = await client.delete_query(9)
        req.assert_called_once_with("DELETE", "/queries/9")
        assert result is True


@pytest.mark.asyncio
async def test_star_query(client):
    mock = {"id": 9, "starred": True}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.star_query(9)
        req.assert_called_once_with("PATCH", "/queries/9/star")


@pytest.mark.asyncio
async def test_unstar_query(client):
    mock = {"id": 9, "starred": False}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.unstar_query(9)
        req.assert_called_once_with("PATCH", "/queries/9/unstar")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest test_client_queries.py -v 2>&1 | tail -5
```

Expected: `AttributeError: 'OpenProjectClient' object has no attribute 'get_queries'`

- [ ] **Step 3: Append client methods to `src/client.py`**

Append after the last method in the file (`delete_cost_entry`):

```python
    async def get_queries(self, project_id: int | None = None) -> dict:
        """List saved queries, optionally scoped to a project."""
        if project_id is not None:
            from urllib.parse import quote as _quote
            import json as _json
            filters = _quote(_json.dumps([{"project_id": {"operator": "=", "values": [str(project_id)]}}]))
            return await self._request("GET", f"/queries?filters={filters}")
        return await self._request("GET", "/queries")

    async def get_query(self, query_id: int) -> dict:
        """Get a saved query by ID."""
        return await self._request("GET", f"/queries/{query_id}")

    async def get_default_query(self, project_id: int | None = None) -> dict:
        """Get the default query (global or project-scoped)."""
        if project_id is not None:
            return await self._request("GET", f"/projects/{project_id}/queries/default")
        return await self._request("GET", "/queries/default")

    async def create_query(self, data: dict) -> dict:
        """Create a new saved query. `data` is the full HAL payload."""
        return await self._request("POST", "/queries", data)

    async def update_query(self, query_id: int, data: dict) -> dict:
        """Update a saved query. `data` is the partial HAL payload."""
        return await self._request("PATCH", f"/queries/{query_id}", data)

    async def delete_query(self, query_id: int) -> bool:
        """Delete a saved query by ID."""
        await self._request("DELETE", f"/queries/{query_id}")
        return True

    async def star_query(self, query_id: int) -> dict:
        """Star a query (pin to top of the list)."""
        return await self._request("PATCH", f"/queries/{query_id}/star")

    async def unstar_query(self, query_id: int) -> dict:
        """Unstar a query."""
        return await self._request("PATCH", f"/queries/{query_id}/unstar")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest test_client_queries.py -v 2>&1 | tail -5
```

Expected: `10 passed`

- [ ] **Step 5: Commit**

```bash
git add src/client.py test_client_queries.py
git commit -m "feat(phase-c): add query client methods"
```

---

### Task 2: Queries tool module

**Files:**
- Create: `src/tools/queries.py`
- Create: `test_queries.py`

**Interfaces:**
- Consumes: all 8 client methods from Task 1
- Produces MCP tools: `list_queries`, `get_query`, `get_default_query`, `create_query`, `update_query`, `delete_query`, `star_query`, `unstar_query`

The key helper `_build_query_payload` translates the simplified tool inputs into the HAL payload the API expects.

- [ ] **Step 1: Write the failing test**

Create `test_queries.py`:

```python
"""Unit tests for query tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_queries_empty():
    mock = _mock_client({"get_queries": {"_embedded": {"elements": []}}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import list_queries
        result = await list_queries.fn()
        assert "no queries" in result.lower() or "0" in result


async def test_list_queries_results():
    queries = [{"id": 1, "name": "Open bugs", "public": False}]
    mock = _mock_client({"get_queries": {"_embedded": {"elements": queries}}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import list_queries
        result = await list_queries.fn()
        assert "Open bugs" in result


async def test_get_query():
    q = {"id": 7, "name": "My query", "public": True, "_links": {"project": {"title": "infra"}}}
    mock = _mock_client({"get_query": q})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import get_query
        result = await get_query.fn(query_id=7)
        assert "My query" in result
        assert "7" in result


async def test_get_default_query():
    q = {"id": 1, "name": "Default", "public": True, "_links": {}}
    mock = _mock_client({"get_default_query": q})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import get_default_query
        result = await get_default_query.fn()
        assert "Default" in result


async def test_create_query_minimal():
    created = {"id": 9, "name": "Test Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query
        result = await create_query.fn(name="Test Query")
        assert "9" in result or "Test Query" in result
        mock.create_query.assert_called_once()
        payload = mock.create_query.call_args[0][0]
        assert payload["name"] == "Test Query"


async def test_create_query_with_columns_and_sort():
    created = {"id": 10, "name": "Sorted Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query
        result = await create_query.fn(
            name="Sorted Query",
            column_names=["id", "subject", "status"],
            sort_by="updatedAt-desc",
        )
        payload = mock.create_query.call_args[0][0]
        assert payload["_links"]["columns"] == [
            {"href": "/api/v3/queries/columns/id"},
            {"href": "/api/v3/queries/columns/subject"},
            {"href": "/api/v3/queries/columns/status"},
        ]
        assert payload["_links"]["sortBy"] == [{"href": "/api/v3/queries/sort_bys/updatedAt-desc"}]


async def test_create_query_with_project():
    created = {"id": 11, "name": "Project Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query
        await create_query.fn(name="Project Query", project_id=4)
        payload = mock.create_query.call_args[0][0]
        assert payload["_links"]["project"] == {"href": "/api/v3/projects/4"}


async def test_update_query():
    updated = {"id": 9, "name": "Renamed"}
    mock = _mock_client({"update_query": updated})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import update_query
        result = await update_query.fn(query_id=9, name="Renamed")
        assert "Renamed" in result or "9" in result
        payload = mock.update_query.call_args[0][1]
        assert payload["name"] == "Renamed"


async def test_delete_query():
    mock = _mock_client({"delete_query": True})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import delete_query
        result = await delete_query.fn(query_id=9)
        assert "deleted" in result.lower()
        mock.delete_query.assert_called_once_with(9)


async def test_star_query():
    mock = _mock_client({"star_query": {"id": 9}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import star_query
        result = await star_query.fn(query_id=9)
        assert "starred" in result.lower()
        mock.star_query.assert_called_once_with(9)


async def test_unstar_query():
    mock = _mock_client({"unstar_query": {"id": 9}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import unstar_query
        result = await unstar_query.fn(query_id=9)
        assert "unstarred" in result.lower()
        mock.unstar_query.assert_called_once_with(9)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest test_queries.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError` on `src.tools.queries`

- [ ] **Step 3: Create `src/tools/queries.py`**

```python
"""Query (saved view) management tools for OpenProject."""

from typing import Any

from src.server import get_client, mcp
from src.utils.formatting import format_error


def _build_query_payload(
    name: str,
    project_id: int | None = None,
    column_names: list[str] | None = None,
    sort_by: str | None = None,
    public: bool = False,
) -> dict[str, Any]:
    """Build a HAL query payload from simplified inputs.

    Args:
        name: Query name
        project_id: Optional project to scope the query to
        column_names: Column identifiers in display order
            (e.g. ["id", "subject", "status", "assignee", "dueDate"])
        sort_by: Sort spec in '{column}-{asc|desc}' format
            (e.g. "updatedAt-desc", "dueDate-asc")
        public: Whether the query is visible to all project members
    """
    links: dict[str, Any] = {}
    if project_id is not None:
        links["project"] = {"href": f"/api/v3/projects/{project_id}"}
    if column_names:
        links["columns"] = [
            {"href": f"/api/v3/queries/columns/{col}"} for col in column_names
        ]
    if sort_by:
        links["sortBy"] = [{"href": f"/api/v3/queries/sort_bys/{sort_by}"}]
    return {"name": name, "public": public, "_links": links}


@mcp.tool(tags={"read", "queries"})
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
            return "✅ No saved queries found."
        text = f"✅ **Saved queries** ({len(queries)}):\n\n"
        for q in queries:
            public = "🌐 public" if q.get("public") else "🔒 private"
            starred = " ⭐" if q.get("starred") else ""
            text += f"- **{q.get('name', 'Unnamed')}** (ID: {q.get('id', 'N/A')}) — {public}{starred}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list queries: {e!s}")


@mcp.tool(tags={"read", "queries"})
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
            col_names = [c.get("title") or c.get("href", "").split("/")[-1] for c in columns]
            text += f"**Columns**: {', '.join(col_names)}\n"
        sort_by = links.get("sortBy", [])
        if sort_by:
            sorts = [s.get("title") or s.get("href", "").split("/")[-1] for s in sort_by]
            text += f"**Sort by**: {', '.join(sorts)}\n"
        filters = q.get("filters", [])
        if filters:
            text += f"**Filters** ({len(filters)}):\n"
            for f in filters:
                f_links = f.get("_links", {})
                fname = f_links.get("filter", {}).get("title") or f_links.get("filter", {}).get("href", "").split("/")[-1]
                op = f_links.get("operator", {}).get("title") or f_links.get("operator", {}).get("href", "").split("/")[-1]
                text += f"  - {fname}: {op}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get query: {e!s}")


@mcp.tool(tags={"read", "queries"})
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
            col_names = [c.get("title") or c.get("href", "").split("/")[-1] for c in columns]
            text += f"**Columns**: {', '.join(col_names)}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get default query: {e!s}")


@mcp.tool(tags={"write", "queries"})
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


@mcp.tool(tags={"write", "queries"})
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
        links: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if public is not None:
            data["public"] = public
        if column_names is not None:
            links["columns"] = [
                {"href": f"/api/v3/queries/columns/{col}"} for col in column_names
            ]
        if sort_by is not None:
            links["sortBy"] = [{"href": f"/api/v3/queries/sort_bys/{sort_by}"}]
        if links:
            data["_links"] = links
        if not data:
            return format_error("No fields provided to update.")
        q = await client.update_query(query_id, data)
        return f"✅ Query #{query_id} updated: '{q.get('name', query_id)}'\n"
    except Exception as e:
        return format_error(f"Failed to update query: {e!s}")


@mcp.tool(tags={"write", "queries"})
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


@mcp.tool(tags={"write", "queries"})
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


@mcp.tool(tags={"write", "queries"})
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest test_queries.py -v 2>&1 | tail -10
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add src/tools/queries.py test_queries.py
git commit -m "feat(phase-c): add query tools (list, get, create, update, delete, star, unstar)"
```

---

### Task 3: Register + full test suite + PR

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Add `queries` import to `src/server.py`**

In the alphabetical `from src.tools import (  # noqa: F401` block, add `queries` between `projects` and `relations`:

```python
        projects,  # 7 tools
        queries,   # 8 tools: list_queries, get_query, get_default_query, create_query, update_query, delete_query, star_query, unstar_query
        relations,  # 5 tools
```

(The log line is now dynamic — no manual count update needed.)

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -q 2>&1 | tail -5
```

Expected: ≥143 passed (132 existing + 10 client + 11 tool = 153 total), 0 failed.

- [ ] **Step 3: Verify ruff and mypy**

```bash
uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501 --output-format=concise 2>&1 | grep -v "^warning" | tail -3
uv run mypy src/ --ignore-missing-imports 2>&1 | grep -v "^warning\|VIRTUAL_ENV" | tail -3
```

Expected: `All checks passed!` and `Found 0 errors`

- [ ] **Step 4: Smoke test — confirm queries tools registered**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python -c "
import asyncio, os
from src.server import mcp
async def main():
    tools = await mcp.get_tools()
    q_tools = [n for n in tools if 'quer' in n]
    print(f'Total: {len(tools)}, query tools: {sorted(q_tools)}')
asyncio.run(main())
" 2>&1 | grep -v "INFO\|warning\|VIRTUAL_ENV"
```

Expected: `Total: 94` and all 8 query tool names listed.

- [ ] **Step 5: Commit**

```bash
git add src/server.py
git commit -m "feat(phase-c): register queries module; 86→94 tools"
```

- [ ] **Step 6: Push and open PR**

```bash
git push -u origin feature/phase-c-queries

gh pr create \
  --title "feat(phase-c): add query (saved view) management tools" \
  --body "$(cat <<'EOF'
## Summary

Phase C of the full API coverage roadmap. Adds 8 query management tools (86 → 94).

Queries are OpenProject's saved work-package views — every board, list, Gantt, and calendar configuration is a query. Without this, an AI agent can't persist or recall any filtered WP view between sessions.

| Tool | Tags | What it does |
|---|---|---|
| \`list_queries\` | read, queries | List saved queries (global or project-scoped) |
| \`get_query\` | read, queries | Get query details incl. filters, columns, sort order |
| \`get_default_query\` | read, queries | Get the default view configuration |
| \`create_query\` | write, queries | Create a named view with columns, sort, and optional project scope |
| \`update_query\` | write, queries | Rename or change columns/sort of an existing query |
| \`delete_query\` | write, queries | Permanently delete a saved query |
| \`star_query\` | write, queries | Pin a query to the top of the list |
| \`unstar_query\` | write, queries | Unpin a query |

The tool layer accepts simple strings for column names and sort specs (`"updatedAt-desc"`) and constructs the nested HAL `_links` payload internally via `_build_query_payload`.

## Test plan
- [ ] \`uv run pytest -q\` → ≥143 passed, 0 failed
- [ ] \`uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501\` → 0 errors
- [ ] \`uv run mypy src/ --ignore-missing-imports\` → 0 errors
- [ ] Smoke test shows 94 tools registered, 8 query tools present
EOF
)"
```

- [ ] **Step 7: Do NOT merge — stop here**

---

## Self-Review

**Spec coverage:**
- `list_queries` ✅ Task 2
- `get_query` ✅ Task 2
- `get_default_query` ✅ Task 2
- `create_query` ✅ Task 2
- `update_query` ✅ Task 2
- `delete_query` ✅ Task 2
- `star_query` ✅ Task 2
- `unstar_query` ✅ Task 2
- All client methods tested ✅ Task 1
- Server registration ✅ Task 3
- Category tag `"queries"` on all 8 tools ✅ Task 2

**Placeholder scan:** None found — all steps have complete code and expected outputs.

**Type consistency:**
- `_build_query_payload(name, project_id, column_names, sort_by, public)` defined in Task 2 and used internally by `create_query` tool ✅
- `client.create_query(data: dict)` called with `payload` from `_build_query_payload` ✅
- `client.update_query(query_id: int, data: dict)` called with `data` dict in `update_query` tool ✅
- Test for `create_query` verifies `mock.create_query.call_args[0][0]` shape ✅

**Note on filters:** The plan deliberately omits a `filters` parameter on `create_query`/`update_query`. The HAL filter structure (with `_type`, `_links.filter`, `_links.operator`, primitive vs link values) is complex enough that supporting it requires its own serialization layer. The tools as designed support the most common use case (columns + sort + project scope). Filters can be added as a follow-up once the basic query CRUD is in place.
