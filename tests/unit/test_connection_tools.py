#!/usr/bin/env python3
"""Unit tests for connection tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.connection import check_permissions, test_connection

# Unwrap FunctionTool wrappers so tools are directly callable


async def test_test_connection():
    with patch("src.tools.connection.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(
            return_value={
                "instanceVersion": "17.5.1",
                "coreVersion": "17",
                "_type": "Root",
            }
        )
        mock_get_client.return_value = mock_client
        result = await test_connection()
        assert "✅" in result, f"Expected ✅ in result, got: {result}"
        assert "API connection successful!" in result, (
            f"Expected success message, got: {result}"
        )
        assert "**Instance Version**:" in result, (
            f"Expected Instance Version in result, got: {result}"
        )
        assert "17.5.1" in result, f"Expected version in result, got: {result}"
        print("✅ test_test_connection passed")


async def test_check_permissions():
    with patch("src.tools.connection.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.check_permissions = AsyncMock(
            return_value={
                "name": "Tom Gerke",
                "email": "tom@example.com",
                "login": "tom",
                "status": "active",
                "admin": True,
            }
        )
        mock_get_client.return_value = mock_client
        result = await check_permissions()
        assert "✅" in result, f"Expected ✅ in result, got: {result}"
        assert "User Permissions Retrieved" in result, (
            f"Expected permissions header, got: {result}"
        )
        assert "**Name**:" in result, f"Expected Name field in result, got: {result}"
        assert "Tom Gerke" in result, f"Expected name in result, got: {result}"
        print("✅ test_check_permissions passed")
