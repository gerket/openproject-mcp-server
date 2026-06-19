"""Unit tests for workflow-aware status transition validation (network-free).

_request is replaced with a recorder that simulates: get_work_package (current
status + lockVersion), the /form allowedValues, and the final PATCH. Run:
  uv run pytest test_client_transitions.py
"""

import asyncio

import pytest

from src.client import OpenProjectClient


def _client(current_status_id, allowed_status_ids):
    """Client whose _request simulates a WP in `current_status_id` whose form
    permits transitions to `allowed_status_ids`."""
    c = OpenProjectClient(base_url="https://op.test", api_key="k")
    calls = []

    async def fake_request(method, endpoint, data=None):
        calls.append((method, endpoint, data))
        if method == "GET" and endpoint.startswith("/work_packages/"):
            return {
                "id": 1,
                "lockVersion": 9,
                "_links": {"status": {"href": f"/api/v3/statuses/{current_status_id}"}},
            }
        if endpoint.endswith("/form"):
            return {
                "_embedded": {
                    "schema": {
                        "status": {
                            "_embedded": {
                                "allowedValues": [
                                    {"id": sid, "name": f"S{sid}"}
                                    for sid in allowed_status_ids
                                ]
                            }
                        }
                    }
                }
            }
        return {"id": 1, "subject": "ok"}  # the PATCH

    c._request = fake_request  # type: ignore[assignment]
    return c, calls


def test_allowed_transition_proceeds():
    c, calls = _client(current_status_id=1, allowed_status_ids=[1, 7, 12])
    asyncio.run(c.update_work_package(1, {"status_id": 7}))
    # last call must be the PATCH (transition was permitted)
    assert calls[-1][0] == "PATCH"


def test_disallowed_transition_raises_with_options():
    c, calls = _client(current_status_id=1, allowed_status_ids=[1, 7])
    with pytest.raises(Exception) as exc:
        asyncio.run(c.update_work_package(1, {"status_id": 99}))
    msg = str(exc.value)
    assert "not allowed" in msg
    assert "S7" in msg  # lists the valid options
    # never reached the PATCH
    assert not any(call[0] == "PATCH" for call in calls)


def test_same_status_skips_form_check():
    # setting status to the current value shouldn't trigger a /form lookup
    c, calls = _client(current_status_id=7, allowed_status_ids=[1, 7, 12])
    asyncio.run(c.update_work_package(1, {"status_id": 7}))
    assert not any(call[1].endswith("/form") for call in calls)
    assert calls[-1][0] == "PATCH"


def test_validate_flag_false_skips_check():
    # opt-out: no /form lookup, PATCH proceeds even to an "unlisted" status
    c, calls = _client(current_status_id=1, allowed_status_ids=[1])
    asyncio.run(
        c.update_work_package(1, {"status_id": 99, "validate_status_transition": False})
    )
    assert not any(call[1].endswith("/form") for call in calls)
    assert calls[-1][0] == "PATCH"
