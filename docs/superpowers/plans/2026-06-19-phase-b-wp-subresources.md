# Phase B: Work Package Sub-Resources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 9 new tools covering work package watchers, activity editing, available assignees, and reminders — completing the WP interaction surface.

**Architecture:** Two new tool modules (`src/tools/watchers.py`, `src/tools/reminders.py`) plus one new client method on the activities endpoint. Client methods append to `src/client.py` after `delete_cost_entry`. Both modules registered in `src/server.py`. Tests follow the existing `test_*.py` pattern at repo root (pytest-asyncio auto mode, `.fn()` for decorated tools).

**Tech Stack:** Python 3.10+, FastMCP, Pydantic v2, pytest-asyncio

## Global Constraints

- Worktree: `/Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/phase-b-wp-subresources`
- All commands run from the worktree root
- Every `@mcp.tool` must carry `tags={"read"}` or `tags={"write"}` — no bare decorators
- Tests: `async def test_*` functions, `.fn()` to call decorated tools, `conftest.py` sets env vars (already exists)
- Run tests with: `uv run pytest <file> -v`
- All source changes must pass: `uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501` and `uv run mypy src/ --ignore-missing-imports`
- Conventional commit messages; one commit per task
- `src/server.py` tool count comment must be updated when new modules are added

## New tools summary

| Tool | Tag | Endpoint |
|---|---|---|
| `list_watchers` | read | `GET /work_packages/{id}/watchers` |
| `list_available_watchers` | read | `GET /work_packages/{id}/available_watchers` |
| `add_watcher` | write | `POST /work_packages/{id}/watchers` — body: `{"_links": {"user": {"href": "/api/v3/users/{user_id}"}}}` |
| `remove_watcher` | write | `DELETE /work_packages/{id}/watchers/{user_id}` |
| `get_activity` | read | `GET /activities/{id}` |
| `update_activity` | write | `PATCH /activities/{id}` — body: `{"comment": {"raw": "..."}, "internal": false}` |
| `list_available_assignees` | read | `GET /work_packages/{id}/available_assignees` |
| `list_reminders` | read | `GET /work_packages/{id}/reminders` |
| `create_reminder` | write | `POST /work_packages/{id}/reminders` — body: `{"remindAt": "ISO8601", "note": "..."}` |

## File map

| File | Action | Notes |
|---|---|---|
| `src/client.py` | Modify (append) | 6 new async methods after `delete_cost_entry` |
| `src/tools/watchers.py` | Create | `list_watchers`, `list_available_watchers`, `add_watcher`, `remove_watcher`, `get_activity`, `update_activity`, `list_available_assignees` — 7 tools |
| `src/tools/reminders.py` | Create | `list_reminders`, `create_reminder` — 2 tools |
| `src/server.py` | Modify | Add `watchers` and `reminders` imports; update count 77→88 |
| `test_watchers.py` | Create | Unit tests for all 7 watcher/activity/assignee tools |
| `test_reminders.py` | Create | Unit tests for both reminder tools |

---

### Task 1: Client methods — watchers, activities, assignees, reminders

**Files:**
- Modify: `src/client.py` (append after `delete_cost_entry`)

**Interfaces:**
- Produces:
  - `async def get_watchers(self, work_package_id: int) -> dict`
  - `async def get_available_watchers(self, work_package_id: int) -> dict`
  - `async def add_watcher(self, work_package_id: int, user_id: int) -> bool`
  - `async def remove_watcher(self, work_package_id: int, user_id: int) -> bool`
  - `async def get_activity(self, activity_id: int) -> dict`
  - `async def update_activity(self, activity_id: int, comment: str, internal: bool = False) -> dict`
  - `async def get_available_assignees(self, work_package_id: int) -> dict`
  - `async def get_reminders(self, work_package_id: int) -> dict`
  - `async def create_reminder(self, work_package_id: int, remind_at: str, note: str | None = None) -> dict`

- [ ] **Step 1: Write the failing test**

Create `test_client_subresources.py`:

```python
"""Unit tests for WP sub-resource client methods (network-free)."""

import pytest

from src.client import OpenProjectClient
from unittest.mock import AsyncMock, patch


def _client() -> OpenProjectClient:
    return OpenProjectClient(base_url="https://op.test", api_key="k")


@pytest.fixture
def client():
    return _client()


@pytest.mark.asyncio
async def test_get_watchers(client):
    mock = {"_embedded": {"elements": [{"id": 5, "name": "Tom"}]}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.get_watchers(42)
        req.assert_called_once_with("GET", "/work_packages/42/watchers")
        assert result == mock


@pytest.mark.asyncio
async def test_get_available_watchers(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_available_watchers(42)
        req.assert_called_once_with("GET", "/work_packages/42/available_watchers")


@pytest.mark.asyncio
async def test_add_watcher(client):
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as req:
        result = await client.add_watcher(42, 5)
        req.assert_called_once_with(
            "POST",
            "/work_packages/42/watchers",
            {"_links": {"user": {"href": "/api/v3/users/5"}}},
        )
        assert result is True


@pytest.mark.asyncio
async def test_remove_watcher(client):
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as req:
        result = await client.remove_watcher(42, 5)
        req.assert_called_once_with("DELETE", "/work_packages/42/watchers/5")
        assert result is True


@pytest.mark.asyncio
async def test_get_activity(client):
    mock = {"id": 7, "comment": {"raw": "hello"}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.get_activity(7)
        req.assert_called_once_with("GET", "/activities/7")
        assert result == mock


@pytest.mark.asyncio
async def test_update_activity(client):
    mock = {"id": 7, "comment": {"raw": "updated"}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.update_activity(7, "updated", internal=False)
        req.assert_called_once_with(
            "PATCH",
            "/activities/7",
            {"comment": {"raw": "updated"}, "internal": False},
        )
        assert result == mock


@pytest.mark.asyncio
async def test_get_available_assignees(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_available_assignees(42)
        req.assert_called_once_with("GET", "/work_packages/42/available_assignees")


@pytest.mark.asyncio
async def test_get_reminders(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_reminders(42)
        req.assert_called_once_with("GET", "/work_packages/42/reminders")


@pytest.mark.asyncio
async def test_create_reminder(client):
    mock = {"id": 3, "remindAt": "2026-06-25T09:00:00Z"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.create_reminder(42, "2026-06-25T09:00:00Z", note="review")
        req.assert_called_once_with(
            "POST",
            "/work_packages/42/reminders",
            {"remindAt": "2026-06-25T09:00:00Z", "note": "review"},
        )
        assert result == mock
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest test_client_subresources.py -v 2>&1 | tail -10
```

Expected: `AttributeError: 'OpenProjectClient' object has no attribute 'get_watchers'`

- [ ] **Step 3: Append client methods to `src/client.py`**

Append after the `delete_cost_entry` method (the last method in the file):

```python
    async def get_watchers(self, work_package_id: int) -> dict:
        """List users watching a work package."""
        return await self._request("GET", f"/work_packages/{work_package_id}/watchers")

    async def get_available_watchers(self, work_package_id: int) -> dict:
        """List users eligible to watch a work package (project members)."""
        return await self._request(
            "GET", f"/work_packages/{work_package_id}/available_watchers"
        )

    async def add_watcher(self, work_package_id: int, user_id: int) -> bool:
        """Add a user as a watcher on a work package."""
        await self._request(
            "POST",
            f"/work_packages/{work_package_id}/watchers",
            {"_links": {"user": {"href": f"/api/v3/users/{user_id}"}}},
        )
        return True

    async def remove_watcher(self, work_package_id: int, user_id: int) -> bool:
        """Remove a user from the watcher list of a work package."""
        await self._request(
            "DELETE", f"/work_packages/{work_package_id}/watchers/{user_id}"
        )
        return True

    async def get_activity(self, activity_id: int) -> dict:
        """Get a single work package activity (comment or change) by ID."""
        return await self._request("GET", f"/activities/{activity_id}")

    async def update_activity(
        self, activity_id: int, comment: str, internal: bool = False
    ) -> dict:
        """Edit the comment on an activity. Requires 'edit journals' permission."""
        return await self._request(
            "PATCH",
            f"/activities/{activity_id}",
            {"comment": {"raw": comment}, "internal": internal},
        )

    async def get_available_assignees(self, work_package_id: int) -> dict:
        """List users eligible to be assigned to a work package."""
        return await self._request(
            "GET", f"/work_packages/{work_package_id}/available_assignees"
        )

    async def get_reminders(self, work_package_id: int) -> dict:
        """List reminders set on a work package for the current user."""
        return await self._request(
            "GET", f"/work_packages/{work_package_id}/reminders"
        )

    async def create_reminder(
        self, work_package_id: int, remind_at: str, note: str | None = None
    ) -> dict:
        """Create a reminder on a work package.

        Args:
            work_package_id: Work package ID
            remind_at: ISO 8601 datetime string (e.g. '2026-06-25T09:00:00Z')
            note: Optional reminder note
        """
        payload: dict = {"remindAt": remind_at}
        if note:
            payload["note"] = note
        return await self._request(
            "POST", f"/work_packages/{work_package_id}/reminders", payload
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest test_client_subresources.py -v 2>&1 | tail -10
```

Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add src/client.py test_client_subresources.py
git commit -m "feat(phase-b): add client methods for watchers, activities, assignees, reminders"
```

---

### Task 2: Watchers + activity + assignees tool module

**Files:**
- Create: `src/tools/watchers.py`
- Create: `test_watchers.py`

**Interfaces:**
- Consumes: `client.get_watchers`, `client.get_available_watchers`, `client.add_watcher`, `client.remove_watcher`, `client.get_activity`, `client.update_activity`, `client.get_available_assignees` (from Task 1)
- Produces MCP tools: `list_watchers`, `list_available_watchers`, `add_watcher`, `remove_watcher`, `get_activity`, `update_activity`, `list_available_assignees`

- [ ] **Step 1: Write the failing test**

Create `test_watchers.py`:

```python
"""Unit tests for watchers, activity, and available_assignees tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_watchers_empty():
    mock = _mock_client({"get_watchers": {"_embedded": {"elements": []}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_watchers
        result = await list_watchers.fn(work_package_id=42)
        assert "no watchers" in result.lower() or "0" in result


async def test_list_watchers_results():
    watchers = [{"id": 5, "name": "Tom Gerke"}]
    mock = _mock_client({"get_watchers": {"_embedded": {"elements": watchers}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_watchers
        result = await list_watchers.fn(work_package_id=42)
        assert "Tom Gerke" in result


async def test_list_available_watchers():
    users = [{"id": 5, "name": "Tom Gerke"}, {"id": 4, "name": "Admin"}]
    mock = _mock_client({"get_available_watchers": {"_embedded": {"elements": users}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_available_watchers
        result = await list_available_watchers.fn(work_package_id=42)
        assert "Tom Gerke" in result
        assert "Admin" in result


async def test_add_watcher():
    mock = _mock_client({"add_watcher": True})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import add_watcher
        result = await add_watcher.fn(work_package_id=42, user_id=5)
        assert "added" in result.lower() or "watching" in result.lower()
        mock.add_watcher.assert_called_once_with(42, 5)


async def test_remove_watcher():
    mock = _mock_client({"remove_watcher": True})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import remove_watcher
        result = await remove_watcher.fn(work_package_id=42, user_id=5)
        assert "removed" in result.lower()
        mock.remove_watcher.assert_called_once_with(42, 5)


async def test_get_activity():
    activity = {
        "id": 7,
        "comment": {"raw": "Fixed the bug.", "html": "<p>Fixed the bug.</p>"},
        "createdAt": "2026-06-19T10:00:00Z",
        "_links": {"user": {"title": "Tom Gerke"}},
    }
    mock = _mock_client({"get_activity": activity})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import get_activity
        result = await get_activity.fn(activity_id=7)
        assert "Fixed the bug" in result
        assert "Tom Gerke" in result


async def test_update_activity():
    updated = {
        "id": 7,
        "comment": {"raw": "Updated comment.", "html": "<p>Updated comment.</p>"},
    }
    mock = _mock_client({"update_activity": updated})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import update_activity
        result = await update_activity.fn(activity_id=7, comment="Updated comment.")
        assert "updated" in result.lower()
        mock.update_activity.assert_called_once_with(7, "Updated comment.", internal=False)


async def test_list_available_assignees():
    users = [{"id": 5, "name": "Tom Gerke"}]
    mock = _mock_client({"get_available_assignees": {"_embedded": {"elements": users}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_available_assignees
        result = await list_available_assignees.fn(work_package_id=42)
        assert "Tom Gerke" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest test_watchers.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError` or `ImportError` on `src.tools.watchers`

- [ ] **Step 3: Create `src/tools/watchers.py`**

```python
"""Watcher, activity, and available-assignee tools for OpenProject work packages."""

from src.server import get_client, mcp
from src.utils.formatting import format_error


@mcp.tool(tags={"read"})
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


@mcp.tool(tags={"read"})
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


@mcp.tool(tags={"write"})
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


@mcp.tool(tags={"write"})
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


@mcp.tool(tags={"read"})
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


@mcp.tool(tags={"write"})
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


@mcp.tool(tags={"read"})
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest test_watchers.py -v 2>&1 | tail -10
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add src/tools/watchers.py test_watchers.py
git commit -m "feat(phase-b): add watchers, activity edit, and available_assignees tools"
```

---

### Task 3: Reminders tool module

**Files:**
- Create: `src/tools/reminders.py`
- Create: `test_reminders.py`

**Interfaces:**
- Consumes: `client.get_reminders`, `client.create_reminder` (from Task 1)
- Produces MCP tools: `list_reminders`, `create_reminder`

- [ ] **Step 1: Write the failing test**

Create `test_reminders.py`:

```python
"""Unit tests for reminder tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_reminders_empty():
    mock = _mock_client({"get_reminders": {"_embedded": {"elements": []}}})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import list_reminders
        result = await list_reminders.fn(work_package_id=42)
        assert "no reminders" in result.lower() or "0" in result


async def test_list_reminders_results():
    reminders = [
        {
            "id": 3,
            "remindAt": "2026-06-25T09:00:00Z",
            "note": "Review this",
            "completed": False,
        }
    ]
    mock = _mock_client({"get_reminders": {"_embedded": {"elements": reminders}}})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import list_reminders
        result = await list_reminders.fn(work_package_id=42)
        assert "Review this" in result
        assert "2026-06-25" in result


async def test_create_reminder():
    created = {"id": 3, "remindAt": "2026-06-25T09:00:00Z", "note": "Don't forget"}
    mock = _mock_client({"create_reminder": created})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import create_reminder
        result = await create_reminder.fn(
            work_package_id=42,
            remind_at="2026-06-25T09:00:00Z",
            note="Don't forget",
        )
        assert "3" in result or "created" in result.lower()
        mock.create_reminder.assert_called_once_with(
            42, "2026-06-25T09:00:00Z", note="Don't forget"
        )


async def test_create_reminder_no_note():
    created = {"id": 4, "remindAt": "2026-06-26T09:00:00Z"}
    mock = _mock_client({"create_reminder": created})
    with patch("src.tools.reminders.get_client", return_value=mock):
        from src.tools.reminders import create_reminder
        result = await create_reminder.fn(
            work_package_id=42,
            remind_at="2026-06-26T09:00:00Z",
        )
        mock.create_reminder.assert_called_once_with(
            42, "2026-06-26T09:00:00Z", note=None
        )
        assert "4" in result or "created" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest test_reminders.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError` on `src.tools.reminders`

- [ ] **Step 3: Create `src/tools/reminders.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest test_reminders.py -v 2>&1 | tail -5
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/tools/reminders.py test_reminders.py
git commit -m "feat(phase-b): add list_reminders and create_reminder tools"
```

---

### Task 4: Register modules in server.py + full test suite

**Files:**
- Modify: `src/server.py`

**Interfaces:**
- Consumes: `src.tools.watchers` (7 tools), `src.tools.reminders` (2 tools)
- Produces: all 9 new tools available at runtime; tool count updated 77→86

- [ ] **Step 1: Edit `src/server.py` — add imports and update count**

In the `from src.tools import (  # noqa: F401` block, add `reminders` and `watchers` in alphabetical order:

```python
    from src.tools import (  # noqa: F401
        attachments,  # 4 tools
        connection,  # 2 tools
        costs,  # 5 tools
        groups,  # 2 tools
        hierarchy,  # 3 tools
        memberships,  # 5 tools
        news,  # 5 tools
        notifications,  # 3 tools
        projects,  # 7 tools
        relations,  # 5 tools
        reminders,  # 2 tools: list_reminders, create_reminder
        time_entries,  # 5 tools
        users,  # 6 tools
        versions,  # 2 tools
        watchers,  # 7 tools: list_watchers, list_available_watchers, add_watcher, remove_watcher, get_activity, update_activity, list_available_assignees
        weekly_reports,  # 4 tools
        wiki,  # 1 tool
        work_packages,  # 18 tools
    )

    logger.info("✅ All 86 tools loaded successfully (50 read, 36 write)")
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -v 2>&1 | tail -15
```

Expected: ≥119 passed (110 existing + 9 new: test_client_subresources 9 + test_watchers 8 + test_reminders 4 = 121 total), 0 failed.

- [ ] **Step 3: Verify ruff and mypy are clean**

```bash
uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501 --output-format=concise 2>&1 | grep -v "^warning" | tail -3
uv run mypy src/ --ignore-missing-imports 2>&1 | grep -v "^warning\|VIRTUAL_ENV" | tail -3
```

Expected: `All checks passed!` and `Found 0 errors`

- [ ] **Step 4: Commit**

```bash
git add src/server.py
git commit -m "feat(phase-b): register watchers and reminders modules; tool count 77→86"
```

---

### Task 5: Push and open PR

- [ ] **Step 1: Final smoke test**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python -c "
import asyncio, os
from src.server import mcp
async def main():
    tools = await mcp.get_tools()
    new = [n for n in tools if any(x in n for x in ['watcher','reminder','activity','assignee'])]
    print(f'Total tools: {len(tools)}')
    print('New tools:', sorted(new))
asyncio.run(main())
" 2>&1 | grep -v "INFO\|warning\|VIRTUAL_ENV"
```

Expected: `Total tools: 86` and all 9 new tool names listed.

- [ ] **Step 2: Push and open PR**

```bash
git push -u origin feature/phase-b-wp-subresources

gh pr create \
  --title "feat(phase-b): add WP sub-resources — watchers, activity edit, available assignees, reminders" \
  --body "$(cat <<'EOF'
## Summary

Adds 9 new tools covering work package sub-resources (Phase B of the full API coverage roadmap).

**New tools (77 → 86):**

| Tool | Tag | What it does |
|---|---|---|
| `list_watchers` | read | Who is watching a WP |
| `list_available_watchers` | read | Who *can* watch (project members) — for autocomplete |
| `add_watcher` | write | Add a user as watcher |
| `remove_watcher` | write | Remove a watcher |
| `get_activity` | read | Fetch a single activity/comment by ID |
| `update_activity` | write | Edit a posted comment (requires 'edit journals' permission) |
| `list_available_assignees` | read | Who can be assigned — scoped to project role, better than list_users |
| `list_reminders` | read | Reminders set by the current user on a WP |
| `create_reminder` | write | Set a reminder with date + optional note |

## Test plan
- [ ] `uv run pytest -q` → ≥119 passed, 0 failed
- [ ] `uv run ruff check src/ --select E,F,W,I,UP,B,RUF --ignore E501` → 0 errors
- [ ] `uv run mypy src/ --ignore-missing-imports` → 0 errors
- [ ] Tool count smoke test shows 86 tools
EOF
)"
```

- [ ] **Step 3: Do NOT merge — stop here**

---

## Self-Review

**Spec coverage (from master plan Phase B):**
- `list_watchers` ✅ Task 2
- `list_available_watchers` ✅ Task 2
- `add_watcher` ✅ Task 2
- `remove_watcher` ✅ Task 2
- `get_activity` ✅ Task 2
- `update_activity` ✅ Task 2
- `list_available_assignees` ✅ Task 2
- `list_reminders` ✅ Task 3
- `create_reminder` ✅ Task 3
- All client methods tested ✅ Task 1
- Server registration ✅ Task 4
- Tool count updated ✅ Task 4

**Placeholder scan:** None found. All steps have complete code, commands, and expected outputs.

**Type consistency:**
- `get_watchers(work_package_id: int) -> dict` — used in Task 1 test and Task 2 `list_watchers` tool ✅
- `add_watcher(work_package_id: int, user_id: int) -> bool` — used in Task 1 test and Task 2 `add_watcher` tool ✅
- `update_activity(activity_id: int, comment: str, internal: bool = False) -> dict` — used in Task 1 test (`update_activity(7, "updated", internal=False)`) and Task 2 tool ✅
- `create_reminder(work_package_id: int, remind_at: str, note: str | None = None) -> dict` — used in Task 1 test and Task 3 tool ✅
