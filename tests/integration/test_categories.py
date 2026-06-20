"""Integration tests: categories."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_categories(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_project_categories(project_id)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_get_category(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_project_categories(project_id)
    categories = result.get("_embedded", {}).get("elements", [])
    if not categories:
        pytest.skip(
            f"No categories in project #{project_id} — "
            "create one at Project settings → Work packages → Categories → + Category"
        )
    cat_id = categories[0]["id"]
    fetched = await client.get_category(cat_id)
    assert fetched.get("id") == cat_id
