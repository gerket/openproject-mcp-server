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
        pytest.skip("No memberships in test project — run setup script first")
    m_id = members[0]["id"]
    fetched = await client.get_membership(m_id)
    assert fetched["id"] == m_id


async def test_membership_lifecycle(
    client: OpenProjectClient,
    bot_client: OpenProjectClient | None,
    project_id: int,
) -> None:
    """Full create/get/update/delete lifecycle using the bot user on the test project.

    The bot's existing membership is removed, re-created, updated, then restored
    to its original state in the finally block so the project is left clean.
    """
    if bot_client is None:
        pytest.skip(
            "OPENPROJECT_BOT_API_KEY not set — bot user needed for membership lifecycle test"
        )

    # Discover the bot user's ID from their own token
    bot_me = await bot_client.check_permissions()
    bot_id = int(bot_me["id"])

    # Find and remove the bot's existing membership (if any) so we can re-add it
    all_memberships = extract_elements(
        await client.get_memberships(project_id=project_id)
    )
    existing = next(
        (
            m
            for m in all_memberships
            if m.get("_links", {})
            .get("principal", {})
            .get("href", "")
            .endswith(f"/{bot_id}")
        ),
        None,
    )
    original_role_ids = []
    if existing:
        original_role_ids = [
            r["href"].rstrip("/").split("/")[-1]
            for r in existing.get("_links", {}).get("roles", [])
        ]
        await client.delete_membership(existing["id"])

    # Find an assignable project role
    roles_result = await client.get_roles()
    roles = roles_result.get("_embedded", {}).get("elements", [])
    system_names = {"anonymous", "non member", "non-member"}
    candidates = [r for r in roles if r.get("name", "").lower() not in system_names]

    created = None
    role_id = None
    for r in candidates:
        try:
            created = await client.create_membership(
                {"project_id": project_id, "user_id": bot_id, "role_ids": [r["id"]]}
            )
            role_id = r["id"]
            break
        except Exception as e:
            if "unassignable" in str(e).lower():
                continue
            raise

    if created is None:
        pytest.skip("No assignable project-level roles found on this instance")

    m_id = created["id"]
    try:
        fetched = await client.get_membership(m_id)
        assert fetched["id"] == m_id

        updated = await client.update_membership(m_id, {"role_ids": [role_id]})
        assert updated["id"] == m_id

        await client.delete_membership(m_id)
    finally:
        # Restore original bot membership if it existed
        if original_role_ids:
            try:
                await client.create_membership(
                    {
                        "project_id": project_id,
                        "user_id": bot_id,
                        "role_ids": original_role_ids,
                    }
                )
            except Exception:
                pass
