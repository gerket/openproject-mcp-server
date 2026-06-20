#!/usr/bin/env python3
"""Unit tests for memberships tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.memberships import (
    CreateMembershipInput,
    create_membership,
    delete_membership,
    list_memberships,
)

# Unwrap FunctionTool wrappers so tools are directly callable
list_memberships = list_memberships.fn
create_membership = create_membership.fn
delete_membership = delete_membership.fn


async def test_list_memberships():
    with patch("src.tools.memberships.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_memberships = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {
                            "id": 1,
                            "_links": {
                                "principal": {
                                    "title": "Tom Gerke",
                                    "href": "/api/v3/users/5",
                                },
                                "project": {"title": "infrastructure"},
                                "roles": [{"title": "Member"}],
                            },
                        }
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_memberships(project_id=4)
        assert "Tom Gerke" in result, f"Expected Tom Gerke in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_list_memberships passed")


async def test_list_memberships_empty():
    with patch("src.tools.memberships.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_memberships = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_memberships(project_id=4)
        assert "No memberships found" in result, (
            f"Expected empty message, got: {result}"
        )
        print("✅ test_list_memberships_empty passed")


async def test_create_membership():
    with patch("src.tools.memberships.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_membership = AsyncMock(
            return_value={
                "id": 42,
                "_embedded": {
                    "project": {"name": "infrastructure"},
                    "principal": {"name": "Tom Gerke"},
                    "roles": [{"name": "Member"}],
                },
            }
        )
        mock_get_client.return_value = mock_client
        result = await create_membership(
            CreateMembershipInput(project_id=4, user_id=5, role_id=1)
        )
        assert "42" in result, f"Expected membership ID in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_create_membership passed")


async def test_delete_membership():
    with patch("src.tools.memberships.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_membership = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_membership(42)
        assert "✅" in result, f"Expected success emoji, got: {result}"
        assert "deleted" in result.lower(), (
            f"Expected 'deleted' in result, got: {result}"
        )
        print("✅ test_delete_membership passed")
