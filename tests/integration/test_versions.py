"""Integration tests: versions."""

import time

import pytest

from src.client import OpenProjectClient
from tests.integration.conftest import extract_elements

pytestmark = pytest.mark.integration


async def test_list_versions(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_versions(project_id)
    assert isinstance(extract_elements(result), list)


async def test_version_lifecycle(client: OpenProjectClient, project_id: int) -> None:
    name = f"integration-test-version-{int(time.time())}"
    result = await client.create_version(project_id, {"name": name})
    v_id = result.get("id")
    assert v_id, f"No id in created version: {result}"

    try:
        versions = extract_elements(await client.get_versions(project_id))
        ids = [v["id"] for v in versions]
        assert v_id in ids, f"Newly created version {v_id} not in list: {ids}"

        updated = await client.update_version(
            v_id, {"name": name + "-updated", "status": "locked"}
        )
        assert updated.get("name") == name + "-updated"
        assert updated.get("status") == "locked"
    finally:
        await client.delete_version(v_id)

    remaining = [
        v["id"] for v in extract_elements(await client.get_versions(project_id))
    ]
    assert v_id not in remaining, f"Version {v_id} still present after delete"
