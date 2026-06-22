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
from src.utils.formatting import format_work_package_detail


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


def _make_wp(*, custom_fields=None, description="A description.", parent=True):
    wp = {
        "id": 929,
        "subject": "Phase J — tool catalog",
        "lockVersion": 3,
        "startDate": "2026-06-01",
        "dueDate": "2026-06-30",
        "percentageDone": 10,
        "createdAt": "2026-06-01T10:00:00Z",
        "updatedAt": "2026-06-20T12:00:00Z",
        "_embedded": {
            "status": {"name": "New", "isClosed": False},
            "type": {"name": "Feature"},
            "priority": {"name": "High"},
        },
        "_links": {
            "assignee": {"title": "Tom Gerke"},
            "author": {"title": "Tom Gerke"},
            "project": {
                "title": "openproject-mcp-server",
                "href": "/api/v3/projects/50",
            },
        },
    }
    if parent:
        wp["_links"]["parent"] = {
            "title": "OpenProject MCP server — tool build-out",
            "href": "/api/v3/work_packages/916",
        }
    if description is None:
        pass  # no description key
    else:
        wp["description"] = {"raw": description}
    if custom_fields:
        wp.update(custom_fields)
    return wp


def _make_form(labels=None):
    schema = {}
    if labels:
        for key, label in labels.items():
            schema[key] = {"name": label}
    return {"_embedded": {"schema": schema}}


def _make_relation(rel_type, to_id, to_subject):
    return {
        "type": rel_type,
        "_embedded": {
            "from": {"id": 929, "subject": "Phase J — tool catalog"},
            "to": {"id": to_id, "subject": to_subject},
        },
    }


def _make_activity(user, comment, created_at="2026-06-20T09:00:00Z"):
    return {
        "id": 1,
        "_type": "Activity::Comment",
        "createdAt": created_at,
        "comment": {"raw": comment},
        "_links": {"user": {"title": user}},
    }


def test_format_full_response():
    wp = _make_wp(custom_fields={"customField3": "5"})
    form = _make_form({"customField3": "Story Points"})
    relations = [_make_relation("blocks", 930, "get_work_package tool")]
    activities = [_make_activity("Tom Gerke", "Scoped out the approach.")]
    result = format_work_package_detail(wp, form, relations, activities)

    assert "## WP #929:" in result
    assert "Phase J" in result
    assert "**Status**: New" in result
    assert "**Type**: Feature" in result
    assert "**Priority**:" in result
    assert "High" in result
    assert "Tom Gerke" in result
    assert "#916" in result
    assert "### Description" in result
    assert "A description." in result
    assert "### Custom Fields" in result
    assert "Story Points" in result
    assert "customField3" in result
    assert "### Relations" in result
    assert "blocks" in result
    assert "#930" in result
    assert "### Activity" in result
    assert "Scoped out the approach." in result


def test_format_empty_sections():
    wp = _make_wp(description=None, parent=False)
    wp.pop("description", None)
    form = _make_form()
    result = format_work_package_detail(wp, form, [], [])

    assert "### Description" in result
    assert "_No description._" in result
    assert "### Custom Fields" in result
    assert "_None._" in result
    assert "### Relations" in result
    assert "_None._" in result
    assert "### Activity" in result
    assert "_No comments._" in result


def test_format_form_fetch_failed():
    wp = _make_wp(custom_fields={"customField3": "5"})
    result = format_work_package_detail(wp, None, [], [])
    assert "### Custom Fields" in result
    assert "_Unavailable (fetch error)._" in result


def test_format_relations_fetch_failed():
    wp = _make_wp()
    form = _make_form()
    result = format_work_package_detail(wp, form, None, [])
    assert "### Relations" in result
    assert "_Unavailable (fetch error)._" in result


def test_format_activities_fetch_failed():
    wp = _make_wp()
    form = _make_form()
    result = format_work_package_detail(wp, form, [], None)
    assert "### Activity" in result
    assert "_Unavailable (fetch error)._" in result
