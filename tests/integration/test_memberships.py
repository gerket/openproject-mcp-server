"""Integration tests: project memberships."""

import pytest

from src.client import OpenProjectClient
from tests.integration.conftest import extract_elements

pytestmark = pytest.mark.integration


async def test_list_memberships(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_memberships(project_id=project_id)
    assert isinstance(extract_elements(result), list)


async def test_get_membership(client: OpenProjectClient, project_id: int) -> None:
    result = await client.get_memberships(project_id=project_id)
    members = extract_elements(result)
    if not members:
        pytest.skip("No memberships in project — add a member to test get_membership")
    m_id = members[0]["id"]
    fetched = await client.get_membership(m_id)
    assert fetched["id"] == m_id


async def test_membership_lifecycle(
    client: OpenProjectClient, project_id: int, current_user_id: int
) -> None:
    # Get a role to assign — filter to non-system roles (assignable as member roles)
    roles_result = await client.get_roles()
    roles = roles_result.get("_embedded", {}).get("elements", [])
    # System roles like "Anonymous", "Non member" can't be used as member roles
    system_names = {"anonymous", "non member", "non-member"}
    assignable = [r for r in roles if r.get("name", "").lower() not in system_names]
    if not assignable:
        pytest.skip("No assignable member roles available")
    role_id = assignable[0]["id"]

    try:
        created = await client.create_membership(
            {
                "project_id": project_id,
                "user_id": current_user_id,
                "role_ids": [role_id],
            }
        )
    except Exception as e:
        if "unassignable role" in str(e).lower() or "422" in str(e):
            pytest.skip(
                f"Role {role_id} is not assignable as a member role on this instance: {e}"
            )
        raise
    m_id = created.get("id")
    assert m_id, f"No id in created membership: {created}"

    try:
        updated = await client.update_membership(m_id, {"role_ids": [role_id]})
        assert updated.get("id") == m_id
    finally:
        await client.delete_membership(m_id)
