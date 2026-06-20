#!/usr/bin/env python3
"""Unit tests for work packages tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.work_packages import (
    CreateWorkPackageInput,
    create_work_package,
    delete_work_package,
    list_priorities,
    list_statuses,
    list_types,
    list_work_packages,
    search_work_packages,
)

# Unwrap FunctionTool wrappers so tools are directly callable


async def test_list_work_packages_empty():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_work_packages = AsyncMock(
            return_value={"_embedded": {"elements": []}, "total": 0}
        )
        mock_get_client.return_value = mock_client
        result = await list_work_packages()
        assert "No work packages found" in result, (
            f"Expected empty message, got: {result}"
        )
        print("✅ test_list_work_packages_empty passed")


async def test_list_work_packages_results():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_work_packages = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {
                            "id": 10,
                            "subject": "Fix bug",
                            "_embedded": {
                                "type": {"name": "Bug"},
                                "status": {"name": "New"},
                                "priority": {"name": "Normal"},
                            },
                        },
                        {
                            "id": 11,
                            "subject": "Add feature",
                            "_embedded": {
                                "type": {"name": "Feature"},
                                "status": {"name": "In Progress"},
                                "priority": {"name": "High"},
                            },
                        },
                    ]
                },
                "total": 2,
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_work_packages()
        assert "Fix bug" in result, f"Expected 'Fix bug' in result, got: {result}"
        assert "Add feature" in result, (
            f"Expected 'Add feature' in result, got: {result}"
        )
        print("✅ test_list_work_packages_results passed")


async def test_search_work_packages():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_work_packages = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {
                            "id": 22,
                            "subject": "login issue",
                            "_embedded": {
                                "type": {"name": "Bug"},
                                "status": {"name": "New"},
                                "priority": {"name": "High"},
                            },
                        }
                    ]
                },
                "total": 1,
            }
        )
        mock_get_client.return_value = mock_client
        result = await search_work_packages(query="login issue")
        assert "login issue" in result, f"Expected subject in result, got: {result}"
        print("✅ test_search_work_packages passed")


async def test_search_work_packages_empty():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_work_packages = AsyncMock(
            return_value={"_embedded": {"elements": []}, "total": 0}
        )
        mock_get_client.return_value = mock_client
        result = await search_work_packages(query="nonexistent")
        assert "No work packages found" in result or "nonexistent" in result, (
            f"Expected empty-search message, got: {result}"
        )
        print("✅ test_search_work_packages_empty passed")


async def test_create_work_package():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_work_package = AsyncMock(
            return_value={
                "id": 55,
                "subject": "New task",
                "_embedded": {
                    "type": {"name": "Task"},
                    "status": {"name": "New"},
                    "priority": {"name": "Normal"},
                },
            }
        )
        mock_get_client.return_value = mock_client
        result = await create_work_package(
            CreateWorkPackageInput(project_id=4, subject="New task", type_id=1)
        )
        assert "55" in result, f"Expected WP ID in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_create_work_package passed")


async def test_delete_work_package():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_work_package = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_work_package(55)
        assert "✅" in result, f"Expected success emoji, got: {result}"
        assert "deleted" in result.lower(), (
            f"Expected 'deleted' in result, got: {result}"
        )
        print("✅ test_delete_work_package passed")


async def test_list_types():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_types = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [{"id": 1, "name": "Bug"}, {"id": 2, "name": "Feature"}]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_types()
        assert "Bug" in result, f"Expected 'Bug' in result, got: {result}"
        assert "Feature" in result, f"Expected 'Feature' in result, got: {result}"
        print("✅ test_list_types passed")


async def test_list_statuses():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_statuses = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 1, "name": "New", "position": 1},
                        {"id": 2, "name": "In Progress", "position": 2},
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_statuses()
        assert "New" in result, f"Expected 'New' in result, got: {result}"
        assert "In Progress" in result, (
            f"Expected 'In Progress' in result, got: {result}"
        )
        print("✅ test_list_statuses passed")


async def test_list_priorities():
    with patch("src.tools.work_packages.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_priorities = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {"id": 1, "name": "Low", "position": 1},
                        {"id": 2, "name": "Normal", "position": 2},
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_priorities()
        assert "Low" in result, f"Expected 'Low' in result, got: {result}"
        assert "Normal" in result, f"Expected 'Normal' in result, got: {result}"
        print("✅ test_list_priorities passed")
