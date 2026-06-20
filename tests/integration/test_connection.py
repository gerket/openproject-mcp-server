"""Integration tests: connection and authentication."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_connection(client: OpenProjectClient) -> None:
    result = await client.test_connection()
    assert isinstance(result, dict)
    assert "_type" in result or "instanceVersion" in result or "coreVersion" in result


async def test_check_permissions(client: OpenProjectClient) -> None:
    result = await client.check_permissions()
    assert result.get("id"), "Expected authenticated user id"
    assert result.get("name"), "Expected authenticated user name"
