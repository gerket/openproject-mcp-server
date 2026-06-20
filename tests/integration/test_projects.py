"""Integration tests: projects."""

import pytest

from src.client import OpenProjectClient
from tests.integration.conftest import extract_elements

pytestmark = pytest.mark.integration


async def test_list_projects(client: OpenProjectClient) -> None:
    result = await client.get_projects()
    projects = extract_elements(result)
    assert projects, "Expected at least one project"
    assert all("id" in p and "name" in p for p in projects)


async def test_get_project(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_project(project_id)
    assert result["id"] == project_id
    assert result.get("name"), "Expected project name"


async def test_get_subprojects(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_subprojects(project_id)
    # May be empty — just assert shape
    assert isinstance(extract_elements(result), list)


async def test_create_update_delete_project(client: OpenProjectClient) -> None:
    result = await client.create_project(
        {"name": "integration-test-project", "identifier": "integration-test-project"}
    )
    new_id = result.get("id")
    assert new_id, f"No id in created project: {result}"

    try:
        updated = await client.update_project(
            new_id, {"name": "integration-test-project-updated"}
        )
        assert updated.get("name") == "integration-test-project-updated"
    finally:
        await client.delete_project(new_id)
