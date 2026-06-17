"""Unit tests for custom-field payload construction (network-free).

_request is replaced with a recorder so we can assert that custom_fields entries
land as top-level customField<N> keys in the POST/PATCH payload. Run:
  uv run pytest test_client_custom_fields.py
"""

import asyncio

import pytest

from src.client import OpenProjectClient


def _client_recording():
    """Client whose _request records calls and returns canned responses."""
    c = OpenProjectClient(base_url="https://op.test", api_key="k")
    calls = []

    async def fake_request(method, endpoint, data=None):
        calls.append((method, endpoint, data))
        # create_work_package POSTs to /form first, then /work_packages.
        if endpoint == "/work_packages/form":
            return {"payload": {"_links": {}}, "lockVersion": 3}
        if endpoint.endswith("/form"):
            return {"payload": {}, "lockVersion": 0}
        # get_work_package (for update lockVersion)
        if method == "GET":
            return {"lockVersion": 5, "id": 1}
        return {"id": 1}

    c._request = fake_request  # type: ignore[assignment]
    return c, calls


def test_create_merges_custom_fields_as_top_level_keys():
    c, calls = _client_recording()
    asyncio.run(c.create_work_package({
        "project": 1, "subject": "s", "type": 1,
        "custom_fields": {"customField12": "JIRA-123", "customField7": 42},
    }))
    # last call is the POST /work_packages
    method, endpoint, payload = calls[-1]
    assert (method, endpoint) == ("POST", "/work_packages")
    assert payload["customField12"] == "JIRA-123"
    assert payload["customField7"] == 42


def test_update_merges_custom_fields_as_top_level_keys():
    c, calls = _client_recording()
    asyncio.run(c.update_work_package(1, {
        "subject": "new",
        "custom_fields": {"customField12": "JIRA-999"},
    }))
    method, endpoint, payload = calls[-1]
    assert method == "PATCH"
    assert payload["customField12"] == "JIRA-999"
    assert payload["lockVersion"] == 5      # echoed from get_work_package


def test_no_custom_fields_leaves_payload_clean():
    c, calls = _client_recording()
    asyncio.run(c.update_work_package(1, {"subject": "x"}))
    _, _, payload = calls[-1]
    assert not any(k.startswith("customField") for k in payload)


def test_invalid_custom_field_key_rejected_on_create():
    # Regression for PR review: only customField<N> keys may be merged, so a
    # stray/typo'd key can't inject an arbitrary top-level property.
    c, calls = _client_recording()
    with pytest.raises(ValueError, match="customField"):
        asyncio.run(c.create_work_package({
            "project": 1, "subject": "s", "type": 1,
            "custom_fields": {"subject": "hijack"},
        }))


def test_invalid_custom_field_key_rejected_on_update():
    c, calls = _client_recording()
    with pytest.raises(ValueError, match="customField"):
        asyncio.run(c.update_work_package(1, {
            "custom_fields": {"lockVersion": 999},
        }))
