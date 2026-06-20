#!/usr/bin/env python3
"""Unit tests for groups client methods and tools."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(
        os.environ,
        {
            "OPENPROJECT_URL": "http://test.example.com",
            "OPENPROJECT_API_KEY": "test-key",
        },
    ):
        from src.client import OpenProjectClient

        return OpenProjectClient("http://test.example.com", "test-key")


def _mock_client(method_responses: dict):
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_get_groups_client():
    client = _make_client()
    mock_response = {"_embedded": {"elements": [{"id": 1, "name": "Devs"}]}}
    with patch.object(
        client, "_request", new=AsyncMock(return_value=mock_response)
    ) as mock_req:
        result = await client.get_groups()
        mock_req.assert_called_once_with("GET", "/groups")
        assert result == mock_response
        print("✅ PASSED: get_groups client")


async def test_get_group_client():
    client = _make_client()
    mock_response = {"id": 1, "name": "Devs"}
    with patch.object(
        client, "_request", new=AsyncMock(return_value=mock_response)
    ) as mock_req:
        result = await client.get_group(1)
        mock_req.assert_called_once_with("GET", "/groups/1")
        assert result == mock_response
        print("✅ PASSED: get_group client")


async def test_list_groups_tool():
    groups = [{"id": 1, "name": "Devs"}, {"id": 2, "name": "QA"}]
    mock = _mock_client({"get_groups": {"_embedded": {"elements": groups}}})
    with patch("src.tools.groups.get_client", return_value=mock):
        from src.tools.groups import list_groups

        result = await list_groups()
        assert "Devs" in result
        assert "QA" in result
        print("✅ PASSED: list_groups tool")


async def test_get_group_tool():
    group = {"id": 1, "name": "Devs", "updatedAt": "2026-06-01T00:00:00Z"}
    mock = _mock_client({"get_group": group})
    with patch("src.tools.groups.get_client", return_value=mock):
        from src.tools.groups import get_group

        result = await get_group(group_id=1)
        assert "Devs" in result
        print("✅ PASSED: get_group tool")
