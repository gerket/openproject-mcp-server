#!/usr/bin/env python3
"""Unit tests for projects tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.projects import (
    CreateProjectInput,
    create_project,
    delete_project,
    get_project,
    list_projects,
)

# Unwrap FunctionTool wrappers so tools are directly callable
list_projects = list_projects.fn
get_project = get_project.fn
create_project = create_project.fn
delete_project = delete_project.fn


async def test_list_projects_empty():
    with patch("src.tools.projects.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_projects = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_projects(active_only=True)
        # format_project_list([]) returns "No projects found."
        assert "No projects" in result, f"Expected empty message, got: {result}"
        print("✅ test_list_projects_empty passed")


async def test_list_projects_results():
    with patch("src.tools.projects.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_projects = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 1, "name": "Alpha", "active": True},
                        {"id": 2, "name": "Beta", "active": True},
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_projects(active_only=True)
        assert "Alpha" in result, f"Expected Alpha in result, got: {result}"
        assert "Beta" in result, f"Expected Beta in result, got: {result}"
        print("✅ test_list_projects_results passed")


async def test_get_project():
    with patch("src.tools.projects.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_project = AsyncMock(
            return_value={
                "id": 4,
                "name": "infrastructure",
                "identifier": "infra",
                "active": True,
                "public": False,
            }
        )
        mock_get_client.return_value = mock_client
        result = await get_project(4)
        assert "infrastructure" in result, f"Expected project name, got: {result}"
        print("✅ test_get_project passed")


async def test_create_project():
    with patch("src.tools.projects.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_project = AsyncMock(
            return_value={
                "id": 99,
                "name": "Test Project",
                "identifier": "test-proj",
                "public": False,
                "status": "active",
                "active": True,
            }
        )
        mock_get_client.return_value = mock_client
        result = await create_project(
            CreateProjectInput(name="Test Project", identifier="test-proj")
        )
        assert "99" in result, f"Expected project ID in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_create_project passed")


async def test_delete_project():
    with patch("src.tools.projects.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_project = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_project(99)
        assert "✅" in result, f"Expected success emoji, got: {result}"
        assert "deleted" in result.lower(), (
            f"Expected 'deleted' in result, got: {result}"
        )
        print("✅ test_delete_project passed")
