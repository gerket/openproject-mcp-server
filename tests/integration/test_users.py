"""Integration tests: users and roles."""

import pytest

from src.client import OpenProjectClient
from tests.integration.conftest import extract_elements

pytestmark = pytest.mark.integration


async def test_list_users(client: OpenProjectClient) -> None:
    result = await client.get_users()
    users = extract_elements(result)
    assert users, "Expected at least one user"
    assert all("id" in u for u in users)


async def test_get_current_user(
    client: OpenProjectClient, current_user_id: int
) -> None:
    result = await client.get_user(current_user_id)
    assert result["id"] == current_user_id
    assert result.get("name"), "Expected user name"


async def test_list_roles(client: OpenProjectClient) -> None:
    result = await client.get_roles()
    roles = result.get("_embedded", {}).get("elements", [])
    assert roles, "Expected at least one role"
    assert all("id" in r and "name" in r for r in roles)


async def test_get_role(client: OpenProjectClient) -> None:
    result = await client.get_roles()
    roles = result.get("_embedded", {}).get("elements", [])
    assert roles
    role_id = roles[0]["id"]
    fetched = await client.get_role(role_id)
    assert fetched["id"] == role_id


async def test_list_project_members(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_memberships(project_id=project_id)
    assert isinstance(extract_elements(result), list)


async def test_list_user_projects(
    client: OpenProjectClient, current_user_id: int
) -> None:
    result = await client.get_memberships(user_id=current_user_id)
    assert isinstance(extract_elements(result), list)


async def test_list_principals(client: OpenProjectClient) -> None:
    result = await client.get_principals()
    principals = extract_elements(result)
    assert principals, "Expected at least one principal"
    assert all("id" in p and "name" in p for p in principals)


async def test_list_principals_project_scoped(
    client: OpenProjectClient, project_id: int
) -> None:
    result = await client.get_principals(project_id)
    assert isinstance(extract_elements(result), list)


async def test_create_and_update_user(
    client: OpenProjectClient,
    api_paths: set,
) -> None:
    import time

    login = f"mcp-test-user-{int(time.time())}"
    created = await client.create_user(
        {
            "login": login,
            "first_name": "Delete Me",
            "last_name": "MCP Integration Test",
            "email": f"{login}@example.invalid",
            "password": "Temporary1!Pass",  # some instances require this field
        }
    )
    uid = created.get("id")
    assert uid, f"No id in created user: {created}"
    assert created.get("status") == "active"
    assert "Delete Me" in created.get("name", "")

    try:
        updated = await client.update_user(uid, {"first_name": "Updated"})
        assert updated.get("id") == uid

        # Lock the user (closest thing to delete via API)
        locked = await client.update_user(uid, {"status": "locked"})
        assert locked.get("status") == "locked"
    finally:
        # Best-effort cleanup: lock ensures the account can't be used
        try:
            await client.update_user(uid, {"status": "locked"})
        except Exception:
            pass
