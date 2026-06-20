"""Integration tests: documents."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_list_documents(client: OpenProjectClient) -> None:
    result = await client.get_documents()
    assert isinstance(result.get("_embedded", {}).get("elements", []), list)


async def test_get_document(client: OpenProjectClient) -> None:
    result = await client.get_documents()
    docs = result.get("_embedded", {}).get("elements", [])
    if not docs:
        pytest.skip("No documents on this instance — create one via the web UI first")
    doc_id = docs[0]["id"]
    fetched = await client.get_document(doc_id)
    assert fetched.get("id") == doc_id
