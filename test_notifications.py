#!/usr/bin/env python3
"""Unit tests for notifications client methods and tools."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        from src.client import OpenProjectClient
        return OpenProjectClient("http://test.example.com", "test-key")


def _mock_client(method_responses: dict):
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_get_notifications_client():
    client = _make_client()
    mock_response = {"_embedded": {"elements": []}, "total": 0}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_notifications()
        assert "/notifications" in mock_req.call_args[0][1]
        print("✅ PASSED: get_notifications client")


async def test_mark_notification_read_client():
    client = _make_client()
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as mock_req:
        result = await client.mark_notification_read(42)
        assert result is True
        assert "/notifications/42/read_ian" in mock_req.call_args[0][1]
        print("✅ PASSED: mark_notification_read client")


async def test_mark_all_notifications_read_client():
    client = _make_client()
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as mock_req:
        result = await client.mark_all_notifications_read()
        assert result is True
        assert "read_ian" in mock_req.call_args[0][1]
        print("✅ PASSED: mark_all_notifications_read client")


async def test_list_notifications_tool_empty():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        mock = _mock_client({"get_notifications": {"_embedded": {"elements": []}, "total": 0}})
        with patch("src.tools.notifications.get_client", return_value=mock):
            from src.tools.notifications import list_notifications
            result = await list_notifications.fn()
            assert "no" in result.lower() or "0" in result
            print("✅ PASSED: list_notifications empty")


async def test_list_notifications_tool_with_items():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        items = [{
            "id": 1,
            "subject": "WP #5 updated",
            "reason": "mentioned",
            "createdAt": "2026-06-17T10:00:00Z",
            "readIAN": False,
            "_links": {"resource": {"href": "/api/v3/work_packages/5", "title": "Fix bug"}}
        }]
        mock = _mock_client({"get_notifications": {"_embedded": {"elements": items}, "total": 1}})
        with patch("src.tools.notifications.get_client", return_value=mock):
            from src.tools.notifications import list_notifications
            result = await list_notifications.fn()
            assert "WP #5" in result or "Fix bug" in result or "mentioned" in result
            print("✅ PASSED: list_notifications with items")


async def test_mark_notification_read_tool():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        mock = _mock_client({"mark_notification_read": True})
        with patch("src.tools.notifications.get_client", return_value=mock):
            from src.tools.notifications import mark_notification_read
            result = await mark_notification_read.fn(notification_id=42)
            assert "marked" in result.lower() or "read" in result.lower()
            print("✅ PASSED: mark_notification_read tool")


async def test_mark_all_notifications_read_tool():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        mock = _mock_client({"mark_all_notifications_read": True})
        with patch("src.tools.notifications.get_client", return_value=mock):
            from src.tools.notifications import mark_all_notifications_read
            result = await mark_all_notifications_read.fn()
            assert "all" in result.lower() or "read" in result.lower()
            print("✅ PASSED: mark_all_notifications_read tool")


if __name__ == "__main__":
    asyncio.run(test_get_notifications_client())
    asyncio.run(test_mark_notification_read_client())
    asyncio.run(test_mark_all_notifications_read_client())
    asyncio.run(test_list_notifications_tool_empty())
    asyncio.run(test_list_notifications_tool_with_items())
    asyncio.run(test_mark_notification_read_tool())
    asyncio.run(test_mark_all_notifications_read_tool())
    print("\n✅ All notifications tests passed")
