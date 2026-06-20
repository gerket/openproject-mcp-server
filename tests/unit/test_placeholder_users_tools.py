"""Unit tests for placeholder_users tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.tools.placeholder_users import (
    create_placeholder_user,
    delete_placeholder_user,
    get_placeholder_user,
    list_placeholder_users,
    update_placeholder_user,
)


async def test_list_placeholder_users_empty():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_placeholder_users = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_placeholder_users()
        assert "No placeholder users" in result


async def test_list_placeholder_users_results():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_placeholder_users = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 1, "name": "External Consultant"},
                        {"id": 2, "name": "Design Team"},
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_placeholder_users()
        assert "External Consultant" in result
        assert "Design Team" in result
        assert "(ID: 1)" in result
        assert "✅" in result


async def test_get_placeholder_user():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_placeholder_user = AsyncMock(
            return_value={"id": 1, "name": "External Consultant"}
        )
        mock_get_client.return_value = mock_client
        result = await get_placeholder_user(1)
        assert "External Consultant" in result
        assert "✅" in result


async def test_create_placeholder_user():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_placeholder_user = AsyncMock(
            return_value={"id": 3, "name": "New Placeholder"}
        )
        mock_get_client.return_value = mock_client
        result = await create_placeholder_user("New Placeholder")
        assert "3" in result
        assert "New Placeholder" in result
        assert "✅" in result


async def test_update_placeholder_user():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.update_placeholder_user = AsyncMock(
            return_value={"id": 1, "name": "Renamed Placeholder"}
        )
        mock_get_client.return_value = mock_client
        result = await update_placeholder_user(1, "Renamed Placeholder")
        assert "Renamed Placeholder" in result
        assert "✅" in result


async def test_delete_placeholder_user_success():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_placeholder_user = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_placeholder_user(1)
        assert "deleted" in result.lower()
        assert "✅" in result


async def test_delete_placeholder_user_403():
    with patch("src.tools.placeholder_users.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_placeholder_user = AsyncMock(
            side_effect=Exception("API Error 403")
        )
        mock_get_client.return_value = mock_client
        result = await delete_placeholder_user(1)
        assert "administrator" in result.lower()
