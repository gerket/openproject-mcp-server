"""Unit tests for Phase E user tools: create_user, update_user, list_principals,
get_my_preferences, update_my_preferences."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.tools.users import (
    CreateUserInput,
    UpdateMyPreferencesInput,
    UpdateUserInput,
    create_user,
    get_my_preferences,
    list_principals,
    update_my_preferences,
    update_user,
)


async def test_create_user():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_user = AsyncMock(
            return_value={
                "id": 9,
                "login": "new-user",
                "name": "New User",
                "email": "new@example.com",
                "status": "active",
            }
        )
        mock_get_client.return_value = mock_client
        result = await create_user(
            CreateUserInput(
                login="new-user",
                first_name="New",
                last_name="User",
                email="new@example.com",
            )
        )
        assert "9" in result
        assert "new-user" in result
        assert "⚠️" in result or "password" in result.lower()
        assert "✅" in result


async def test_create_user_403():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_user = AsyncMock(side_effect=Exception("API Error 403"))
        mock_get_client.return_value = mock_client
        result = await create_user(
            CreateUserInput(login="x", first_name="X", last_name="Y", email="x@x.com")
        )
        assert "administrator" in result.lower()


async def test_update_user():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.update_user = AsyncMock(
            return_value={
                "id": 5,
                "name": "Tom Updated",
                "status": "active",
                "admin": False,
            }
        )
        mock_get_client.return_value = mock_client
        result = await update_user(
            UpdateUserInput(user_id=5, first_name="Tom", last_name="Updated")
        )
        assert "5" in result
        assert "✅" in result


async def test_update_user_403():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.update_user = AsyncMock(side_effect=Exception("API Error 403"))
        mock_get_client.return_value = mock_client
        result = await update_user(UpdateUserInput(user_id=99, status="locked"))
        assert "administrator" in result.lower()


async def test_list_principals():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_principals = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 5, "name": "Tom Gerke", "_type": "User"},
                        {"id": 6, "name": "test-group", "_type": "Group"},
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_principals()
        assert "Tom Gerke" in result
        assert "test-group" in result
        assert "User" in result
        assert "Group" in result
        assert "✅" in result


async def test_list_principals_empty():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_principals = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_principals()
        assert "No principals" in result


async def test_get_my_preferences():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_my_preferences = AsyncMock(
            return_value={
                "timeZone": "America/New_York",
                "commentSortDescending": False,
                "warnOnLeavingUnsaved": True,
                "autoHidePopups": False,
                "pauseReminders": False,
            }
        )
        mock_get_client.return_value = mock_client
        result = await get_my_preferences()
        assert "America/New_York" in result
        assert "✅" in result


async def test_update_my_preferences():
    with patch("src.tools.users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.update_my_preferences = AsyncMock(
            return_value={"timeZone": "Europe/Berlin", "pauseReminders": False}
        )
        mock_get_client.return_value = mock_client
        result = await update_my_preferences(
            UpdateMyPreferencesInput(time_zone="Europe/Berlin")
        )
        assert "Europe/Berlin" in result
        assert "✅" in result
