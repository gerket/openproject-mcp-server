"""Integration tests: budgets and cost entries.

GET /cost_types and GET /cost_entries are not in the OpenProject v3 API spec.
These tests skip via the api_paths fixture rather than catching 404s at runtime.
The budget endpoints (GET /budgets/{id}, GET /projects/{id}/budgets) are always
available in standard installations.
"""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_budgets(client: OpenProjectClient, project_id: int) -> None:
    result = await client._request("GET", f"/projects/{project_id}/budgets")
    assert result.get("_type") == "Collection"


async def test_get_budget(client: OpenProjectClient, project_id: int) -> None:
    result = await client._request("GET", f"/projects/{project_id}/budgets")
    budgets = result.get("_embedded", {}).get("elements", [])
    if not budgets:
        pytest.skip("No budgets in test project — create one via the web UI first")
    budget_id = budgets[0]["id"]
    fetched = await client._request("GET", f"/budgets/{budget_id}")
    assert fetched.get("id") == budget_id


async def test_list_cost_types(client: OpenProjectClient, api_paths: set) -> None:
    if "/api/v3/cost_types" not in api_paths:
        pytest.skip(
            "GET /cost_types not in API spec — not available on this instance "
            "(standard OpenProject; cost entry management requires a plugin)"
        )
    result = await client.get_cost_types()
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_cost_entry_lifecycle(
    client: OpenProjectClient, fresh_wp: int, project_id: int, api_paths: set
) -> None:
    if "/api/v3/cost_entries" not in api_paths:
        pytest.skip(
            "GET /cost_entries not in API spec — not available on this instance"
        )
    if "/api/v3/cost_types" not in api_paths:
        pytest.skip("GET /cost_types not in API spec")

    types_result = await client.get_cost_types()
    cost_types = types_result.get("_embedded", {}).get("elements", [])
    if not cost_types:
        pytest.skip(
            "No cost types configured — create one in Administration → Cost types"
        )
    cost_type_id = cost_types[0]["id"]

    import datetime

    today = datetime.date.today().isoformat()
    created = await client.create_cost_entry(
        {
            "project_id": project_id,
            "work_package_id": fresh_wp,
            "cost_type_id": cost_type_id,
            "units": 2.0,
            "spent_on": today,
        }
    )
    e_id = created.get("id")
    assert e_id, f"No id in created cost entry: {created}"

    try:
        listed = await client.get_cost_entries(work_package_id=fresh_wp)
        ids = [e["id"] for e in listed.get("_embedded", {}).get("elements", [])]
        assert e_id in ids

        updated = await client.update_cost_entry(e_id, {"units": 3.0})
        assert updated.get("id") == e_id
    finally:
        await client.delete_cost_entry(e_id)
