"""Integration tests: attachments."""

import pytest

from src.client import OpenProjectClient

pytestmark = pytest.mark.integration


async def test_attachment_lifecycle(client: OpenProjectClient, fresh_wp: int) -> None:
    file_bytes = b"integration test attachment content"

    try:
        created = await client.upload_attachment(
            container_type="work_packages",
            container_id=fresh_wp,
            file_bytes=file_bytes,
            filename="test-attachment.txt",
            content_type="text/plain",
        )
    except Exception as e:
        if "500" in str(e):
            pytest.skip(
                f"Attachment upload returns 500 on this instance (server-side bug): {e}"
            )
        raise
    a_id = created.get("id")
    assert a_id, f"No id in upload response: {created}"

    try:
        listed = await client.list_attachments("work_packages", fresh_wp)
        ids = [e["id"] for e in listed.get("_embedded", {}).get("elements", [])]
        assert a_id in ids, f"Uploaded attachment {a_id} not in list: {ids}"

        fetched = await client.get_attachment(a_id)
        assert fetched["id"] == a_id
    finally:
        ok = await client.delete_attachment(a_id)
        assert ok
