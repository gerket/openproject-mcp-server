"""Integration tests: saved queries."""

import pytest

from src.client import OpenProjectClient
from tests.integration.conftest import extract_elements

pytestmark = pytest.mark.integration


async def test_list_queries(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_queries(project_id)
    assert isinstance(extract_elements(result), list)


async def test_get_default_query(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_default_query(project_id)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"


async def test_query_lifecycle(client: OpenProjectClient, project_id: int) -> None:
    payload = {
        "name": "integration-test-query",
        "_links": {"project": {"href": f"/api/v3/projects/{project_id}"}},
    }
    result = await client.create_query(payload)
    q_id = result.get("id")
    assert q_id, f"No id in created query: {result}"

    try:
        fetched = await client.get_query(q_id)
        assert fetched["id"] == q_id

        updated = await client.update_query(
            q_id, {"name": "integration-test-query-updated"}
        )
        assert updated.get("name") == "integration-test-query-updated"

        starred = await client.star_query(q_id)
        assert starred is not None

        unstarred = await client.unstar_query(q_id)
        assert unstarred is not None
    finally:
        await client.delete_query(q_id)
