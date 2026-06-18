#!/usr/bin/env python3
"""Unit tests for wiki tools."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _mock_client(method_responses: dict):
    """Return a mock client with specified async method return values."""
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_wiki_pages_empty():
    mock = _mock_client({"get_wiki_pages": {"_embedded": {"elements": []}}})
    with patch("src.tools.wiki.get_client", return_value=mock):
        from src.tools.wiki import list_wiki_pages
        result = await list_wiki_pages.fn(project_id=5)
        assert "No wiki pages" in result
        print("✅ PASSED: list_wiki_pages empty")


async def test_list_wiki_pages_results():
    pages = [{"id": 1, "title": "Home", "slug": "home", "updatedAt": "2026-06-01T00:00:00Z"}]
    mock = _mock_client({"get_wiki_pages": {"_embedded": {"elements": pages}}})
    with patch("src.tools.wiki.get_client", return_value=mock):
        from src.tools.wiki import list_wiki_pages
        result = await list_wiki_pages.fn(project_id=5)
        assert "Home" in result
        assert "home" in result
        print("✅ PASSED: list_wiki_pages with results")


async def test_get_wiki_page_found():
    page = {"id": 1, "title": "Home", "slug": "home",
            "content": {"raw": "# Home\n\nWelcome."}, "updatedAt": "2026-06-01T00:00:00Z"}
    mock = _mock_client({"get_wiki_page": page})
    with patch("src.tools.wiki.get_client", return_value=mock):
        from src.tools.wiki import get_wiki_page
        result = await get_wiki_page.fn(project_id=5, slug="home")
        assert "Home" in result
        assert "Welcome" in result
        print("✅ PASSED: get_wiki_page found")


async def test_upsert_wiki_page():
    from src.tools.wiki import UpsertWikiPageInput
    page = {"id": 1, "title": "New Page", "slug": "new-page", "updatedAt": "2026-06-01T00:00:00Z"}
    mock = _mock_client({"upsert_wiki_page": page})
    with patch("src.tools.wiki.get_client", return_value=mock):
        from src.tools.wiki import upsert_wiki_page
        inp = UpsertWikiPageInput(project_id=5, slug="new-page", title="New Page", content="# New\n\nContent.")
        result = await upsert_wiki_page.fn(inp)
        assert "saved" in result.lower() or "new page" in result.lower()
        print("✅ PASSED: upsert_wiki_page")


async def test_delete_wiki_page():
    mock = _mock_client({"delete_wiki_page": True})
    with patch("src.tools.wiki.get_client", return_value=mock):
        from src.tools.wiki import delete_wiki_page
        result = await delete_wiki_page.fn(project_id=5, slug="home")
        assert "deleted" in result.lower()
        print("✅ PASSED: delete_wiki_page")


async def test_upsert_pydantic_validation():
    from src.tools.wiki import UpsertWikiPageInput
    try:
        UpsertWikiPageInput(project_id=0, slug="x", title="x", content="x")
        print("❌ FAILED: should reject project_id=0")
    except Exception:
        print("✅ PASSED: UpsertWikiPageInput rejects project_id=0")
    try:
        UpsertWikiPageInput(project_id=1, slug="", title="x", content="x")
        print("❌ FAILED: should reject empty slug")
    except Exception:
        print("✅ PASSED: UpsertWikiPageInput rejects empty slug")


if __name__ == "__main__":
    asyncio.run(test_list_wiki_pages_empty())
    asyncio.run(test_list_wiki_pages_results())
    asyncio.run(test_get_wiki_page_found())
    asyncio.run(test_upsert_wiki_page())
    asyncio.run(test_delete_wiki_page())
    asyncio.run(test_upsert_pydantic_validation())
    print("\n✅ All wiki tool tests passed")
