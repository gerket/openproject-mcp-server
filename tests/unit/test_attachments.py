#!/usr/bin/env python3
"""Unit tests for attachment client methods and tools."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(
        os.environ,
        {
            "OPENPROJECT_URL": "http://test.example.com",
            "OPENPROJECT_API_KEY": "test-key",
        },
    ):
        from src.client import OpenProjectClient

        return OpenProjectClient("http://test.example.com", "test-key")


def _mock_client(method_responses: dict):
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_upload_attachment_calls_upload_request():
    client = _make_client()
    mock_response = {"id": 99, "fileName": "test.txt"}
    with patch.object(
        client, "_upload_request", new=AsyncMock(return_value=mock_response)
    ) as mock_up:
        result = await client.upload_attachment(
            container_type="work_packages",
            container_id=5,
            file_bytes=b"hello",
            filename="test.txt",
            content_type="text/plain",
        )
        mock_up.assert_called_once_with(
            "/work_packages/5/attachments", b"hello", "test.txt", "text/plain"
        )
        assert result == mock_response
        print("✅ PASSED: upload_attachment delegates to _upload_request")


async def test_get_attachment_client():
    client = _make_client()
    mock_response = {"id": 99, "fileName": "test.txt"}
    with patch.object(
        client, "_request", new=AsyncMock(return_value=mock_response)
    ) as mock_req:
        result = await client.get_attachment(99)
        mock_req.assert_called_once_with("GET", "/attachments/99")
        print("✅ PASSED: get_attachment client")


async def test_delete_attachment_client():
    client = _make_client()
    with patch.object(client, "_request", new=AsyncMock(return_value={})):
        result = await client.delete_attachment(99)
        assert result is True
        print("✅ PASSED: delete_attachment client")


async def test_list_attachments_client():
    client = _make_client()
    mock_response = {"_embedded": {"elements": []}}
    with patch.object(
        client, "_request", new=AsyncMock(return_value=mock_response)
    ) as mock_req:
        result = await client.list_attachments("work_packages", 5)
        mock_req.assert_called_once_with("GET", "/work_packages/5/attachments")
        print("✅ PASSED: list_attachments client")


async def test_upload_attachment_tool_invalid_container():
    with patch.dict(
        os.environ,
        {
            "OPENPROJECT_URL": "http://test.example.com",
            "OPENPROJECT_API_KEY": "test-key",
        },
    ):
        mock = _mock_client({"upload_attachment": {"id": 1, "fileName": "f.txt"}})
        with patch("src.tools.attachments.get_client", return_value=mock):
            from src.tools.attachments import UploadAttachmentInput, upload_attachment

            inp = UploadAttachmentInput(
                container_type="invalid_type",
                container_id=5,
                file_content_base64="aGVsbG8=",
                filename="test.txt",
            )
            result = await upload_attachment(inp)
            assert "error" in result.lower() or "invalid" in result.lower()
            print("✅ PASSED: upload_attachment rejects invalid container_type")


async def test_upload_attachment_tool_valid():
    import base64

    with patch.dict(
        os.environ,
        {
            "OPENPROJECT_URL": "http://test.example.com",
            "OPENPROJECT_API_KEY": "test-key",
        },
    ):
        mock = _mock_client(
            {"upload_attachment": {"id": 99, "fileName": "test.txt", "fileSize": 5}}
        )
        with patch("src.tools.attachments.get_client", return_value=mock):
            from src.tools.attachments import UploadAttachmentInput, upload_attachment

            inp = UploadAttachmentInput(
                container_type="work_packages",
                container_id=5,
                file_content_base64=base64.b64encode(b"hello").decode(),
                filename="test.txt",
            )
            result = await upload_attachment(inp)
            assert "test.txt" in result or "99" in result
            print("✅ PASSED: upload_attachment tool valid")


async def test_list_attachments_tool():
    with patch.dict(
        os.environ,
        {
            "OPENPROJECT_URL": "http://test.example.com",
            "OPENPROJECT_API_KEY": "test-key",
        },
    ):
        items = [
            {
                "id": 1,
                "fileName": "doc.pdf",
                "fileSize": 1024,
                "createdAt": "2026-06-01T00:00:00Z",
            }
        ]
        mock = _mock_client({"list_attachments": {"_embedded": {"elements": items}}})
        with patch("src.tools.attachments.get_client", return_value=mock):
            from src.tools.attachments import list_attachments

            result = await list_attachments(
                container_type="work_packages", container_id=5
            )
            assert "doc.pdf" in result
            print("✅ PASSED: list_attachments tool")
