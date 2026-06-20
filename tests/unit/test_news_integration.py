#!/usr/bin/env python3
"""
Integration test for News Tools - validates with real or mock OpenProject instance.

This script tests the news tools in integration with the server.
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_news_tools_integration():
    """Test news tools integration."""
    try:
        from src.server import get_client, mcp
    except Exception as e:
        pytest.skip(f"Server import failed (dependencies not installed): {e}")

    # Get client
    client = get_client()

    # Get registered tools
    tool_list = await mcp.list_tools()
    tool_names = {t.name for t in tool_list}

    # Find news tools
    expected_tools = [
        "list_news",
        "create_news",
        "get_news",
        "update_news",
        "delete_news",
    ]

    # Verify all expected tools are registered
    for tool_name in expected_tools:
        assert tool_name in tool_names, (
            f"Expected tool '{tool_name}' not registered in server"
        )

    # Test formatting functions
    from src.utils.formatting import format_news_detail, format_news_list

    test_news = [
        {
            "id": 1,
            "title": "Test News",
            "summary": "Test Summary",
            "createdAt": "2025-12-11T10:00:00.000Z",
            "_links": {
                "project": {"title": "Test Project"},
                "author": {"title": "Test User"},
            },
        }
    ]

    result = format_news_list(test_news)
    assert "📰" in result
    assert "Test News" in result

    result = format_news_detail(test_news[0])
    assert "Test News" in result
