"""Unit tests for custom actions tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.custom_actions import (
    execute_custom_action,
    get_custom_action,
    list_custom_actions,
)

list_custom_actions = list_custom_actions.fn
get_custom_action = get_custom_action.fn
execute_custom_action = execute_custom_action.fn


async def test_list_custom_actions_empty():
    with patch("src.tools.custom_actions.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.list_custom_actions = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_custom_actions()
        assert "No custom actions found" in result


async def test_list_custom_actions_results():
    with patch("src.tools.custom_actions.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.list_custom_actions = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 1, "name": "Start Progress"},
                        {
                            "id": 2,
                            "name": "Ready for Review",
                            "description": {"raw": "Moves to review"},
                        },
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_custom_actions()
        assert "Start Progress" in result
        assert "Ready for Review" in result
        assert "Moves to review" in result
        assert "(ID: 1)" in result
        assert "✅" in result


async def test_get_custom_action():
    with patch("src.tools.custom_actions.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_custom_action = AsyncMock(
            return_value={
                "id": 1,
                "name": "Start Progress",
                "description": {"raw": "Transition to In Progress"},
            }
        )
        mock_get_client.return_value = mock_client
        result = await get_custom_action(1)
        assert "Start Progress" in result
        assert "Transition to In Progress" in result
        assert "**Name**" in result
        assert "✅" in result


async def test_execute_custom_action_success():
    with patch("src.tools.custom_actions.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.execute_custom_action = AsyncMock(
            return_value={
                "_embedded": {
                    "workPackage": {
                        "id": 46,
                        "subject": "Implement login",
                        "_links": {"status": {"title": "In Progress"}},
                    }
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await execute_custom_action(1, 46)
        assert "46" in result
        assert "Implement login" in result
        assert "In Progress" in result
        assert "✅" in result


async def test_execute_custom_action_error():
    with patch("src.tools.custom_actions.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.execute_custom_action = AsyncMock(
            side_effect=Exception("Action not applicable to current status")
        )
        mock_get_client.return_value = mock_client
        result = await execute_custom_action(1, 46)
        assert "Failed" in result
        assert "Action not applicable" in result
