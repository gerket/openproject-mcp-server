#!/usr/bin/env python3
"""Unit tests for time entries tools."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.time_entries import (
    list_time_entries, create_time_entry, delete_time_entry,
    list_time_entry_activities, CreateTimeEntryInput
)

# Unwrap FunctionTool wrappers so tools are directly callable
list_time_entries = list_time_entries.fn
create_time_entry = create_time_entry.fn
delete_time_entry = delete_time_entry.fn
list_time_entry_activities = list_time_entry_activities.fn


async def test_list_time_entries_empty():
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries = AsyncMock(return_value={"_embedded": {"elements": []}})
        mock_get_client.return_value = mock_client
        result = await list_time_entries()
        assert "No time entries found." in result, f"Expected empty message, got: {result}"
        print("✅ test_list_time_entries_empty passed")


async def test_list_time_entries_results():
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries = AsyncMock(return_value={"_embedded": {"elements": [
            {"id": 10, "hours": 2.5, "spentOn": "2026-06-19",
             "_embedded": {
                 "workPackage": {"subject": "test", "id": 46},
                 "activity": {"name": "Development"}
             }}
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_time_entries()
        assert "10" in result, f"Expected entry ID in result, got: {result}"
        assert "2.5" in result, f"Expected hours in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_list_time_entries_results passed")


async def test_create_time_entry():
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_time_entry = AsyncMock(return_value={
            "id": 77, "hours": 1.5, "spentOn": "2026-06-19",
            "_embedded": {
                "workPackage": {"subject": "test", "id": 46},
                "activity": {"name": "Development"}
            }
        })
        mock_get_client.return_value = mock_client
        result = await create_time_entry(CreateTimeEntryInput(
            work_package_id=46, hours=1.5, spent_on="2026-06-19", activity_id=3
        ))
        assert "77" in result, f"Expected entry ID in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_create_time_entry passed")


async def test_delete_time_entry():
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_time_entry = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_time_entry(77)
        assert "✅" in result, f"Expected success emoji, got: {result}"
        assert "deleted" in result.lower(), f"Expected 'deleted' in result, got: {result}"
        print("✅ test_delete_time_entry passed")


async def test_list_time_entry_activities_with_results():
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entry_activities = AsyncMock(return_value={"_embedded": {"elements": [
            {"id": 1, "name": "Management"},
            {"id": 3, "name": "Development"}
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_time_entry_activities()
        assert "Management" in result, f"Expected Management in result, got: {result}"
        assert "Development" in result, f"Expected Development in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_list_time_entry_activities_with_results passed")


async def test_list_time_entry_activities_empty_fallback():
    """When activities endpoint returns empty, expect the fallback common activities list."""
    with patch('src.tools.time_entries.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entry_activities = AsyncMock(return_value={"_embedded": {"elements": []}})
        mock_get_client.return_value = mock_client
        result = await list_time_entry_activities()
        # Falls through to the common activities fallback
        assert "Management" in result, f"Expected Management (fallback) in result, got: {result}"
        assert "Development" in result, f"Expected Development (fallback) in result, got: {result}"
        print("✅ test_list_time_entry_activities_empty_fallback passed")

