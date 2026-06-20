"""Integration tests: work package parent-child hierarchy."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_set_and_remove_parent(
    client: OpenProjectClient, project_id: int, wp_type_id: int
) -> None:
    parent = await client.create_work_package(
        {
            "project": project_id,
            "subject": "integration-test-parent",
            "type": wp_type_id,
        }
    )
    child = await client.create_work_package(
        {"project": project_id, "subject": "integration-test-child", "type": wp_type_id}
    )
    parent_id, child_id = parent["id"], child["id"]

    try:
        # Set parent via update_work_package (set_work_package_parent uses the
        # same PATCH endpoint; update_work_package handles _links correctly)
        result = await client.update_work_package(child_id, {"parent_id": parent_id})
        parent_href = result.get("_links", {}).get("parent", {}).get("href", "")
        assert str(parent_id) in parent_href, (
            f"Expected parent {parent_id} in href, got: {parent_href}"
        )

        # List children of parent
        children = await client.list_work_package_children(parent_id)
        child_ids = [c["id"] for c in children.get("_embedded", {}).get("elements", [])]
        assert child_id in child_ids, (
            f"Child {child_id} not in parent {parent_id} children: {child_ids}"
        )

        # Remove parent
        result_after = await client.update_work_package(child_id, {"parent_id": None})
        parent_href_after = (
            result_after.get("_links", {}).get("parent", {}).get("href") or ""
        )
        assert (
            not parent_href_after
            or parent_href_after == "null"
            or parent_href_after == ""
        ), f"Expected null parent after remove, got: {parent_href_after}"
    finally:
        for wp_id in [child_id, parent_id]:
            try:
                await client.delete_work_package(wp_id)
            except Exception:
                pass
