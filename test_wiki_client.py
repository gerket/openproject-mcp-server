#!/usr/bin/env python3
"""Unit tests for wiki client methods (no live API calls)."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        from src.client import OpenProjectClient
        return OpenProjectClient("http://test.example.com", "test-key")


async def test_get_wiki_pages():
    client = _make_client()
    mock_response = {"_embedded": {"elements": [{"id": 1, "title": "Home"}]}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_wiki_pages(project_id=5)
        mock_req.assert_called_once_with("GET", "/projects/5/wiki_pages")
        assert result == mock_response
        print("✅ PASSED: get_wiki_pages")


async def test_get_wiki_page():
    client = _make_client()
    mock_response = {"id": 1, "title": "Home", "content": {"raw": "# Home"}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_wiki_page(project_id=5, slug="home")
        mock_req.assert_called_once_with("GET", "/projects/5/wiki_pages/home")
        assert result == mock_response
        print("✅ PASSED: get_wiki_page")


async def test_upsert_wiki_page():
    client = _make_client()
    mock_response = {"id": 1, "title": "Home", "content": {"raw": "# Updated"}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.upsert_wiki_page(
            project_id=5, slug="home", data={"title": "Home", "content": "# Updated"}
        )
        mock_req.assert_called_once_with(
            "PUT", "/projects/5/wiki_pages/home",
            {"title": "Home", "content": {"raw": "# Updated"}}
        )
        assert result == mock_response
        print("✅ PASSED: upsert_wiki_page")


async def test_delete_wiki_page():
    client = _make_client()
    with patch.object(client, "_request", new=AsyncMock(return_value={})):
        result = await client.delete_wiki_page(project_id=5, slug="home")
        assert result is True
        print("✅ PASSED: delete_wiki_page")


if __name__ == "__main__":
    asyncio.run(test_get_wiki_pages())
    asyncio.run(test_get_wiki_page())
    asyncio.run(test_upsert_wiki_page())
    asyncio.run(test_delete_wiki_page())
    print("\n✅ All wiki client tests passed")
