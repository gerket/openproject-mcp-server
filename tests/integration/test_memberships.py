"""Integration tests: project memberships."""

import time

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
        pytest.skip(
            "No memberships in test project — the membership lifecycle test "
            "creates its own, so run that first or add a member manually."
        )
    m_id = members[0]["id"]
    fetched = await client.get_membership(m_id)
    assert fetched["id"] == m_id


async def test_membership_lifecycle(
    client: OpenProjectClient, current_user_id: int
) -> None:
    """Full create/get/update/delete lifecycle on a throwaway project.

    Uses its own temporary project so there is no pre-existing membership for
    the current user to conflict with — the create step must be a fresh add.
    """
    # Find a project-level member role by probing (the API response does not
    # distinguish project roles from global roles — trial and error is the only way)
    roles_result = await client.get_roles()
    roles = roles_result.get("_embedded", {}).get("elements", [])
    non_system = {
        r["id"]
        for r in roles
        if r.get("name", "").lower() not in {"anonymous", "non member", "non-member"}
    }

    # Create a throwaway project for isolation
    slug = f"mcp-mbr-test-{int(time.time())}"
    proj = await client.create_project(
        {"name": "mcp-membership-test", "identifier": slug, "public": False}
    )
    temp_project_id = proj["id"]

    try:
        # Try each non-system role until one succeeds as a project membership role
        created = None
        role_id = None
        for r in roles:
            if r["id"] not in non_system:
                continue
            try:
                created = await client.create_membership(
                    {
                        "project_id": temp_project_id,
                        "user_id": current_user_id,
                        "role_ids": [r["id"]],
                    }
                )
                role_id = r["id"]
                break
            except Exception as e:
                if "unassignable" in str(e).lower() or "422" in str(e):
                    continue
                raise

        if created is None:
            pytest.skip(
                "No project-level member roles found — all non-system roles are "
                "global roles (not usable in project memberships) on this instance."
            )

        m_id = created.get("id")
        assert m_id, f"No id in created membership: {created}"

        fetched = await client.get_membership(m_id)
        assert fetched["id"] == m_id

        updated = await client.update_membership(m_id, {"role_ids": [role_id]})
        assert updated.get("id") == m_id

        await client.delete_membership(m_id)
    finally:
        try:
            await client.delete_project(temp_project_id)
        except Exception:
            pass
