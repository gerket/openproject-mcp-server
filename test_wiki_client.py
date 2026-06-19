#!/usr/bin/env python3
"""Unit tests for wiki client method (no live API calls)."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        from src.client import OpenProjectClient
        return OpenProjectClient("http://test.example.com", "test-key")


async def test_get_wiki_page_by_id():
    client = _make_client()
    mock_response = {"id": 72, "title": "Home", "content": {"raw": "# Home"}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_wiki_page_by_id(72)
        mock_req.assert_called_once_with("GET", "/wiki_pages/72")
        assert result == mock_response
        print("✅ PASSED: get_wiki_page_by_id")

