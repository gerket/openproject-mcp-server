"""Unit tests for watchers, activity, and available_assignees tools."""

from unittest.mock import AsyncMock, MagicMock, patch


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_watchers_empty():
    mock = _mock_client({"get_watchers": {"_embedded": {"elements": []}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_watchers

        result = await list_watchers(work_package_id=42)
        assert "no watchers" in result.lower() or "0" in result


async def test_list_watchers_results():
    watchers = [{"id": 5, "name": "Tom Gerke"}]
    mock = _mock_client({"get_watchers": {"_embedded": {"elements": watchers}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_watchers

        result = await list_watchers(work_package_id=42)
        assert "Tom Gerke" in result


async def test_list_available_watchers():
    users = [{"id": 5, "name": "Tom Gerke"}, {"id": 4, "name": "Admin"}]
    mock = _mock_client({"get_available_watchers": {"_embedded": {"elements": users}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_available_watchers

        result = await list_available_watchers(work_package_id=42)
        assert "Tom Gerke" in result
        assert "Admin" in result


async def test_add_watcher():
    mock = _mock_client({"add_watcher": True})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import add_watcher

        result = await add_watcher(work_package_id=42, user_id=5)
        assert "added" in result.lower() or "watching" in result.lower()
        mock.add_watcher.assert_called_once_with(42, 5)


async def test_remove_watcher():
    mock = _mock_client({"remove_watcher": True})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import remove_watcher

        result = await remove_watcher(work_package_id=42, user_id=5)
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

        result = await get_activity(activity_id=7)
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

        result = await update_activity(activity_id=7, comment="Updated comment.")
        assert "updated" in result.lower()
        mock.update_activity.assert_called_once_with(
            7, "Updated comment.", internal=False
        )


async def test_list_available_assignees():
    users = [{"id": 5, "name": "Tom Gerke"}]
    mock = _mock_client({"get_available_assignees": {"_embedded": {"elements": users}}})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import list_available_assignees

        result = await list_available_assignees(work_package_id=42)
        assert "Tom Gerke" in result


async def test_get_activity_author_fallback():
    activity = {
        "id": 8,
        "comment": {"raw": "Fallback test.", "html": "<p>Fallback test.</p>"},
        "createdAt": "2026-06-19T11:00:00Z",
        "_links": {"author": {"title": "Admin User"}},
    }
    mock = _mock_client({"get_activity": activity})
    with patch("src.tools.watchers.get_client", return_value=mock):
        from src.tools.watchers import get_activity

        result = await get_activity(activity_id=8)
        assert "Admin User" in result
        assert "Fallback test" in result
