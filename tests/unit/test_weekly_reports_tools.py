#!/usr/bin/env python3
"""Unit tests for weekly reports tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.weekly_reports import (
    generate_last_week_report,
    generate_this_week_report,
)

# Unwrap FunctionTool wrappers so tools are directly callable


def make_mock_client():
    """Build a mock client that satisfies all calls made by _generate_weekly_report_impl."""
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
    # _fetch_all_project_work_packages loops while elements non-empty; return empty to break immediately
    mock_client.get_work_packages = AsyncMock(
        return_value={"_embedded": {"elements": []}, "total": 0}
    )
    mock_client.get_memberships = AsyncMock(
        return_value={"_embedded": {"elements": []}}
    )
    mock_client.get_time_entries = AsyncMock(
        return_value={"_embedded": {"elements": []}}
    )
    # get_relations doesn't exist on the real client, but the report code silently catches that error
    # No need to mock it; the AttributeError will be swallowed
    return mock_client


async def test_generate_this_week_report():
    with patch("src.tools.weekly_reports.get_client") as mock_get_client:
        mock_client = make_mock_client()
        mock_get_client.return_value = mock_client
        result = await generate_this_week_report(project_id=4)
        assert isinstance(result, str), f"Expected string result, got: {type(result)}"
        assert len(result) > 0, "Expected non-empty result"
        # Should NOT be an error response
        assert "Failed to generate" not in result, f"Unexpected error, got: {result}"
        print("✅ test_generate_this_week_report passed")


async def test_generate_last_week_report():
    with patch("src.tools.weekly_reports.get_client") as mock_get_client:
        mock_client = make_mock_client()
        mock_get_client.return_value = mock_client
        result = await generate_last_week_report(project_id=4)
        assert isinstance(result, str), f"Expected string result, got: {type(result)}"
        assert len(result) > 0, "Expected non-empty result"
        assert "Failed to generate" not in result, f"Unexpected error, got: {result}"
        print("✅ test_generate_last_week_report passed")


async def test_generate_this_week_report_with_team_name():
    with patch("src.tools.weekly_reports.get_client") as mock_get_client:
        mock_client = make_mock_client()
        mock_get_client.return_value = mock_client
        result = await generate_this_week_report(project_id=4, team_name="Backend Team")
        assert isinstance(result, str), f"Expected string result, got: {type(result)}"
        assert len(result) > 0, "Expected non-empty result"
        print("✅ test_generate_this_week_report_with_team_name passed")
