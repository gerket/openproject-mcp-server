"""Attachment tools for OpenProject — upload, list, get, delete."""

import base64

from pydantic import BaseModel, Field

from src.server import get_client
from src.tool_registry import tracked_tool
from src.utils.formatting import format_error, format_success

_VALID_CONTAINERS = {"work_packages", "wiki_pages", "projects"}


class UploadAttachmentInput(BaseModel):
    container_type: str = Field(
        ...,
        description="Resource type: 'work_packages', 'wiki_pages', or 'projects'",
    )
    container_id: int = Field(..., description="ID of the resource to attach to", gt=0)
    file_content_base64: str = Field(..., description="Base64-encoded file content")
    filename: str = Field(
        ..., description="Original filename including extension", min_length=1
    )
    content_type: str = Field(
        "application/octet-stream",
        description="MIME type (e.g. 'image/png', 'text/plain')",
    )


@tracked_tool(tags={"write", "attachments", "attachments-write", "upload_attachment"})
async def upload_attachment(input: UploadAttachmentInput) -> str:
    """Upload a file attachment to a work package, wiki page, or project.

    File content must be base64-encoded. Common content_type values:
    'text/plain', 'application/pdf', 'image/png', 'image/jpeg',
    'application/octet-stream' (binary/unknown).

    Args:
        input: Attachment data including container_type, container_id,
               file_content_base64, filename, and content_type

    Returns:
        Success message with attachment ID

    Example:
        {
            "container_type": "work_packages",
            "container_id": 42,
            "file_content_base64": "<base64 string>",
            "filename": "screenshot.png",
            "content_type": "image/png"
        }
    """
    try:
        if input.container_type not in _VALID_CONTAINERS:
            return format_error(
                f"Invalid container_type '{input.container_type}'. "
                f"Must be one of: {', '.join(sorted(_VALID_CONTAINERS))}"
            )
        try:
            file_bytes = base64.b64decode(input.file_content_base64)
        except Exception:
            return format_error(
                "Invalid base64 in file_content_base64 — could not decode."
            )

        client = get_client()
        attachment = await client.upload_attachment(
            container_type=input.container_type,
            container_id=input.container_id,
            file_bytes=file_bytes,
            filename=input.filename,
            content_type=input.content_type,
        )
        att_id = attachment.get("id", "N/A")
        result = format_success("Attachment uploaded successfully.")
        result += f"\n\n**ID**: {att_id}"
        result += f"\n**Filename**: {attachment.get('fileName', input.filename)}"
        size = attachment.get("fileSize")
        if size is not None:
            result += f"\n**Size**: {size:,} bytes"
        return result
    except Exception as e:
        return format_error(f"Failed to upload attachment: {e!s}")


@tracked_tool(tags={"read", "attachments", "attachments-read", "list_attachments"})
async def list_attachments(container_type: str, container_id: int) -> str:
    """List all attachments on a work package, wiki page, or project.

    Args:
        container_type: One of 'work_packages', 'wiki_pages', 'projects'
        container_id: ID of the resource

    Returns:
        List of attachments with IDs, filenames, and sizes
    """
    try:
        if container_type not in _VALID_CONTAINERS:
            return format_error(
                f"Invalid container_type '{container_type}'. "
                f"Must be one of: {', '.join(sorted(_VALID_CONTAINERS))}"
            )
        client = get_client()
        result = await client.list_attachments(container_type, container_id)
        items = result.get("_embedded", {}).get("elements", [])

        if not items:
            return f"No attachments found on {container_type} #{container_id}."

        text = f"✅ **Attachments on {container_type} #{container_id}** ({len(items)}):\n\n"
        for att in items:
            att_id = att.get("id", "N/A")
            fname = att.get("fileName", "unknown")
            size = att.get("fileSize")
            created = att.get("createdAt", "")[:10]
            size_str = f"{size:,} bytes" if size is not None else "unknown size"
            text += f"- **{fname}** (ID: {att_id}, {size_str})"
            if created:
                text += f" — {created}"
            text += "\n"
        return text
    except Exception as e:
        return format_error(f"Failed to list attachments: {e!s}")


@tracked_tool(tags={"read", "attachments", "attachments-read", "get_attachment"})
async def get_attachment(attachment_id: int) -> str:
    """Get metadata for a specific attachment.

    Args:
        attachment_id: The attachment ID

    Returns:
        Attachment details including filename, size, and download link
    """
    try:
        client = get_client()
        att = await client.get_attachment(attachment_id)

        text = f"✅ **Attachment #{att.get('id')}**\n\n"
        text += f"**Filename**: {att.get('fileName', 'Unknown')}\n"
        size = att.get("fileSize")
        if size is not None:
            text += f"**Size**: {size:,} bytes\n"
        if att.get("contentType"):
            text += f"**Type**: {att['contentType']}\n"
        if att.get("createdAt"):
            text += f"**Uploaded**: {att['createdAt'][:10]}\n"
        download = att.get("_links", {}).get("downloadLocation", {}).get("href")
        if download:
            text += f"**Download URL**: {download}\n"
        return text
    except Exception as e:
        return format_error(f"Failed to get attachment: {e!s}")


@tracked_tool(tags={"write", "attachments", "attachments-write", "delete_attachment"})
async def delete_attachment(attachment_id: int) -> str:
    """Delete an attachment permanently.

    WARNING: Cannot be undone.

    Args:
        attachment_id: The attachment ID to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_attachment(attachment_id)
        return format_success(f"Attachment #{attachment_id} deleted.")
    except Exception as e:
        return format_error(f"Failed to delete attachment: {e!s}")
