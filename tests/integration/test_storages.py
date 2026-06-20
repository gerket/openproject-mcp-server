"""Integration tests: storages, project storages, and file links."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_storages(client: OpenProjectClient) -> None:
    result = await client.get_storages()
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_get_storage(client: OpenProjectClient) -> None:
    result = await client.get_storages()
    storages = result.get("_embedded", {}).get("elements", [])
    if not storages:
        pytest.skip(
            "No storages configured — set up one in Administration → File storages"
        )
    storage_id = storages[0]["id"]
    fetched = await client.get_storage(storage_id)
    assert fetched.get("id") == storage_id


async def test_list_project_storages(client: OpenProjectClient) -> None:
    result = await client.get_project_storages()
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_list_work_package_file_links(
    client: OpenProjectClient, fresh_wp: int
) -> None:
    result = await client.get_work_package_file_links(fresh_wp)
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)
