"""Integration tests: news."""

import json

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_news_lifecycle(client: OpenProjectClient, project_id: int) -> None:
    created = await client.create_news(
        {
            "project": project_id,
            "title": "integration-test-news",
            "summary": "Created by integration test",
            "description": "Test body.",
        }
    )
    n_id = created.get("id")
    assert n_id, f"No id in created news: {created}"

    try:
        filters = json.dumps(
            [{"project": {"operator": "=", "values": [str(project_id)]}}]
        )
        listed = await client.get_news(filters=filters, page_size=50)
        ids = [e["id"] for e in listed.get("_embedded", {}).get("elements", [])]
        assert n_id in ids, f"Created news {n_id} not in list: {ids}"

        fetched = await client.get_news_item(n_id)
        assert fetched["id"] == n_id
        assert fetched.get("title") == "integration-test-news"

        updated = await client.update_news(
            n_id, {"title": "integration-test-news-updated"}
        )
        assert updated.get("title") == "integration-test-news-updated"
    finally:
        ok = await client.delete_news(n_id)
        assert ok
