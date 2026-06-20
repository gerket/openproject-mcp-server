"""Unit tests for WP sub-resource client methods (network-free)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.client import OpenProjectClient


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
            {"comment": "updated", "internal": False},
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
