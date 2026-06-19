#!/usr/bin/env python3
"""Unit tests for versions tools."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.versions import list_versions, create_version, CreateVersionInput

# Unwrap FunctionTool wrappers so tools are directly callable
list_versions = list_versions.fn
create_version = create_version.fn



async def test_list_versions_empty():
    with patch('src.tools.versions.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_versions = AsyncMock(return_value={"_embedded": {"elements": []}})
        mock_get_client.return_value = mock_client
        result = await list_versions(4)
        assert "No versions found for project #4." in result, \
            f"Expected empty message, got: {result}"
        print("✅ test_list_versions_empty passed")


async def test_list_versions_results():
    with patch('src.tools.versions.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_versions = AsyncMock(return_value={"_embedded": {"elements": [
            {"id": 8, "name": "v1.0", "status": "open"},
            {"id": 9, "name": "v2.0", "status": "locked"},
        ]}})
        mock_get_client.return_value = mock_client
        result = await list_versions(4)
        assert "v1.0" in result, f"Expected v1.0 in result, got: {result}"
        assert "v2.0" in result, f"Expected v2.0 in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_list_versions_results passed")


async def test_create_version():
    with patch('src.tools.versions.get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_version = AsyncMock(return_value={
            "id": 8, "name": "v1.0", "status": "open"
        })
        mock_get_client.return_value = mock_client
        result = await create_version(CreateVersionInput(project_id=4, name="v1.0"))
        assert "8" in result, f"Expected version ID in result, got: {result}"
        assert "v1.0" in result, f"Expected version name in result, got: {result}"
        assert "**Name**:" in result, f"Expected Name field in result, got: {result}"
        assert "**ID**:" in result, f"Expected ID field in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_create_version passed")


async def run_all():
    tests = [
        test_list_versions_empty,
        test_list_versions_results,
        test_create_version,
    ]
    for t in tests:
        await t()
    print(f"\n✅ All {len(tests)} tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
