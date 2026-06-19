#!/usr/bin/env python3
"""Unit tests for wiki tools.

The OpenProject v3 wiki API is a stub — only GET by integer ID is available.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _mock_client(method_responses: dict):
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_get_wiki_page_found():
    page = {
        "id": 72,
        "title": "Home",
        "slug": "home",
        "content": {"raw": "# Home\n\nWelcome.", "html": "<h1>Home</h1>"},
        "updatedAt": "2026-06-01T00:00:00Z",
    }
    mock = _mock_client({"get_wiki_page_by_id": page})
    with patch.dict(os.environ, {"OPENPROJECT_URL": "http://test.example.com", "OPENPROJECT_API_KEY": "test-key"}):
        with patch("src.tools.wiki.get_client", return_value=mock):
            from src.tools.wiki import get_wiki_page
            result = await get_wiki_page.fn(wiki_page_id=72)
            assert "Home" in result
            assert "Welcome" in result
            print("✅ PASSED: get_wiki_page found")


async def test_get_wiki_page_error():
    mock = MagicMock()
    mock.get_wiki_page_by_id = AsyncMock(side_effect=Exception("API Error 404: Not Found"))
    with patch.dict(os.environ, {"OPENPROJECT_URL": "http://test.example.com", "OPENPROJECT_API_KEY": "test-key"}):
        with patch("src.tools.wiki.get_client", return_value=mock):
            from src.tools.wiki import get_wiki_page
            result = await get_wiki_page.fn(wiki_page_id=999)
            assert "error" in result.lower() or "failed" in result.lower()
            print("✅ PASSED: get_wiki_page error handled")


if __name__ == "__main__":
    asyncio.run(test_get_wiki_page_found())
    asyncio.run(test_get_wiki_page_error())
    print("\n✅ All wiki tool tests passed")
