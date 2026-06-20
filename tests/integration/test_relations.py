"""Integration tests: work package relations."""

import json

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_relation_lifecycle(
    client: OpenProjectClient, project_id: int, wp_type_id: int
) -> None:
    a = await client.create_work_package(
        {
            "project": project_id,
            "subject": "integration-test-relation-A",
            "type": wp_type_id,
        }
    )
    b = await client.create_work_package(
        {
            "project": project_id,
            "subject": "integration-test-relation-B",
            "type": wp_type_id,
        }
    )
    a_id, b_id = a["id"], b["id"]

    try:
        relation = await client.create_work_package_relation(
            {"from_id": a_id, "to_id": b_id, "type": "relates"}
        )
        r_id = relation.get("id")
        assert r_id, f"No id in created relation: {relation}"

        # get
        fetched = await client.get_work_package_relation(r_id)
        assert fetched["id"] == r_id

        # list (filtered to WP A)
        filters = json.dumps([{"involved": {"operator": "=", "values": [str(a_id)]}}])
        result = await client.list_work_package_relations(filters)
        ids = [e["id"] for e in result.get("_embedded", {}).get("elements", [])]
        assert r_id in ids, f"Relation {r_id} not found in list: {ids}"

        # update (change description)
        updated = await client.update_work_package_relation(
            r_id, {"description": "test relation"}
        )
        assert updated.get("id") == r_id

        # delete
        ok = await client.delete_work_package_relation(r_id)
        assert ok
    finally:
        for wp_id in [a_id, b_id]:
            try:
                await client.delete_work_package(wp_id)
            except Exception:
                pass
