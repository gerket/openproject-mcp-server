#!/usr/bin/env python3
"""Unit tests for users tools."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.users import list_users, get_user, list_roles, list_project_members

# Unwrap FunctionTool wrappers so tools are directly callable
list_users = list_users.fn
get_user = get_user.fn
list_roles = list_roles.fn
list_project_members = list_project_members.fn



async def test_list_users():
    with patch('src.tools.users.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_users = AsyncMock(return_value={"_embedded": {"elements": [
            {"id": 5, "name": "Tom Gerke", "email": "tom@test.com", "login": "tom", "status": "active"},
            {"id": 4, "name": "Admin", "email": "admin@test.com", "login": "admin", "status": "active"}
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_users()
        assert "Tom Gerke" in result, f"Expected Tom Gerke in result, got: {result}"
        assert "Admin" in result, f"Expected Admin in result, got: {result}"
        print("✅ test_list_users passed")


async def test_list_users_empty():
    with patch('src.tools.users.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_users = AsyncMock(return_value={"_embedded": {"elements": []}})
        mock_get_client.return_value = mock_client
        result = await list_users()
        assert "No users found" in result, f"Expected empty message, got: {result}"
        print("✅ test_list_users_empty passed")


async def test_get_user():
    with patch('src.tools.users.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_user = AsyncMock(return_value={
            "id": 5, "name": "Tom Gerke", "email": "tom@example.com",
            "login": "tom", "status": "active", "admin": False
        })
        mock_get_client.return_value = mock_client
        result = await get_user(5)
        assert "Tom Gerke" in result, f"Expected name in result, got: {result}"
        assert "tom@example.com" in result, f"Expected email in result, got: {result}"
        print("✅ test_get_user passed")


async def test_list_roles():
    with patch('src.tools.users.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_roles = AsyncMock(return_value={"_embedded": {"elements": [
            {"id": 1, "name": "Member"},
            {"id": 2, "name": "Manager"}
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_roles()
        assert "Member" in result, f"Expected Member in result, got: {result}"
        assert "Manager" in result, f"Expected Manager in result, got: {result}"
        print("✅ test_list_roles passed")


async def test_list_project_members():
    with patch('src.tools.users.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_memberships = AsyncMock(return_value={"_embedded": {"elements": [
            {"_links": {
                "principal": {"title": "Tom Gerke", "href": "/api/v3/users/5"},
                "roles": [{"title": "Member"}]
            }}
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_project_members(4)
        assert "Tom Gerke" in result, f"Expected Tom Gerke in result, got: {result}"
        print("✅ test_list_project_members passed")

