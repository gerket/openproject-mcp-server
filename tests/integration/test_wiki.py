"""Integration tests: wiki pages.

The OpenProject v3 API exposes wiki pages read-only via GET /wiki_pages/{id}.
Write operations (create/update/delete) are not in the v3 API. This test
verifies the read path works if a wiki page exists; otherwise it skips.
"""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_get_wiki_page(client: OpenProjectClient) -> None:
    # Wiki page ID 1 is the default created by OpenProject on project setup.
    # If it doesn't exist on this instance, the test is skipped gracefully.
    try:
        result = await client.get_wiki_page_by_id(1)
        assert result.get("id") == 1 or result.get("_type") is not None
    except Exception as e:
        if "404" in str(e):
            pytest.skip("Wiki page ID 1 not found — create a wiki page first")
        raise
