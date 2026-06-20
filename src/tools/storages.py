"""File storage and file link tools.

File storages (OneDrive, Nextcloud) must be configured in Administration →
File storages before file links can be used. These tools surface what's
configured and allow linking/unlinking files on work packages.
"""

from pydantic import BaseModel, Field

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_success


class CreateFileLinksInput(BaseModel):
    work_package_id: int = Field(
        ..., description="Work package ID to attach files to", gt=0
    )
    storage_id: int = Field(..., description="Storage ID (from list_storages)", gt=0)
    files: list[dict] = Field(
        ...,
        description=(
            "List of file objects from the storage. Each must have: "
            "originId (str), name (str), mimeType (str), "
            "createdAt and lastModifiedAt (ISO datetime strings), fileSize (int)."
        ),
    )


@mcp.tool(tags={"read", "content", "situational", "situational-read", "list_storages"})
async def list_storages() -> str:
    """List configured file storages (OneDrive, Nextcloud, etc.).

    Use this to discover storage IDs before creating file links or browsing files.
    Storages are configured by admins in Administration → File storages.

    Returns:
        List of storages with their IDs, names, and types
    """
    try:
        client = get_client()
        result = await client.get_storages()
        storages = result.get("_embedded", {}).get("elements", [])

        if not storages:
            return (
                "No file storages configured. An admin must set one up at "
                "Administration → File storages before file links can be used."
            )

        text = f"✅ **File Storages ({len(storages)}):**\n\n"
        for s in storages:
            stype = s.get("_links", {}).get("type", {}).get("title", "Unknown")
            text += f"- **{s.get('name', 'Unnamed')}** (ID: {s.get('id', 'N/A')}, type: {stype})\n"
        return text

    except Exception as e:
        return format_error(f"Failed to list storages: {e!s}")


@mcp.tool(tags={"read", "content", "situational", "situational-read", "get_storage"})
async def get_storage(storage_id: int) -> str:
    """Get details of a specific file storage.

    Args:
        storage_id: The storage ID (from list_storages)

    Returns:
        Storage name, type, and configuration details
    """
    try:
        client = get_client()
        s = await client.get_storage(storage_id)

        text = f"✅ **Storage #{s.get('id', storage_id)}:**\n\n"
        text += f"**Name**: {s.get('name', 'N/A')}\n"
        stype = s.get("_links", {}).get("type", {}).get("title", "Unknown")
        text += f"**Type**: {stype}\n"
        if s.get("createdAt"):
            text += f"**Created**: {s['createdAt']}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get storage #{storage_id}: {e!s}")


@mcp.tool(
    tags={"read", "content", "situational", "situational-read", "list_project_storages"}
)
async def list_project_storages(project_id: int | None = None) -> str:
    """List project-storage links — which file storages are enabled on which projects.

    Args:
        project_id: Optional project ID to filter to a specific project

    Returns:
        List of project-storage links
    """
    try:
        client = get_client()
        result = await client.get_project_storages(project_id)
        links = result.get("_embedded", {}).get("elements", [])

        if not links:
            return "No project-storage links found."

        text = f"✅ **Project-Storage Links ({len(links)}):**\n\n"
        for lnk in links:
            lnklinks = lnk.get("_links", {})
            project = lnklinks.get("project", {}).get("title", "Unknown")
            storage = lnklinks.get("storage", {}).get("title", "Unknown")
            text += f"- {project} ↔ {storage} (ID: {lnk.get('id', 'N/A')})\n"
        return text

    except Exception as e:
        return format_error(f"Failed to list project storages: {e!s}")


@mcp.tool(
    tags={
        "read",
        "content",
        "situational",
        "situational-read",
        "list_work_package_file_links",
    }
)
async def list_work_package_file_links(work_package_id: int) -> str:
    """List file links attached to a work package.

    Args:
        work_package_id: The work package ID

    Returns:
        List of file links with names, types, and storage info
    """
    try:
        client = get_client()
        result = await client.get_work_package_file_links(work_package_id)
        links = result.get("_embedded", {}).get("elements", [])

        if not links:
            return f"No file links on work package #{work_package_id}."

        text = f"✅ **File Links on WP #{work_package_id} ({len(links)}):**\n\n"
        for lnk in links:
            od = lnk.get("originData", {})
            text += f"- **{od.get('name', 'Unnamed')}** (ID: {lnk.get('id', 'N/A')})\n"
            if od.get("mimeType"):
                text += f"  Type: {od['mimeType']}\n"
            storage = lnk.get("_links", {}).get("storage", {}).get("title")
            if storage:
                text += f"  Storage: {storage}\n"
        return text

    except Exception as e:
        return format_error(
            f"Failed to list file links for WP #{work_package_id}: {e!s}"
        )


@mcp.tool(tags={"read", "content", "situational", "situational-read", "get_file_link"})
async def get_file_link(file_link_id: int) -> str:
    """Get details of a specific file link.

    Args:
        file_link_id: The file link ID

    Returns:
        File link details including name, type, and storage
    """
    try:
        client = get_client()
        lnk = await client.get_file_link(file_link_id)

        text = f"✅ **File Link #{lnk.get('id', file_link_id)}:**\n\n"
        od = lnk.get("originData", {})
        text += f"**Name**: {od.get('name', 'N/A')}\n"
        if od.get("mimeType"):
            text += f"**Type**: {od['mimeType']}\n"
        if od.get("fileSize"):
            text += f"**Size**: {od['fileSize']} bytes\n"
        storage = lnk.get("_links", {}).get("storage", {}).get("title")
        if storage:
            text += f"**Storage**: {storage}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get file link #{file_link_id}: {e!s}")


@mcp.tool(
    tags={"write", "content", "situational", "situational-write", "create_file_links"}
)
async def create_file_links(input: CreateFileLinksInput) -> str:
    """Attach file links from a storage to a work package.

    Requires a configured file storage. Use list_storages to find the storage_id,
    then supply file metadata from that storage's file browser.

    Args:
        input: Work package ID, storage ID, and list of file objects to link

    Returns:
        Success message with the number of file links created
    """
    try:
        client = get_client()
        result = await client.create_file_links(
            input.work_package_id, input.storage_id, input.files
        )
        created = result.get("_embedded", {}).get("elements", [])
        return format_success(
            f"Created {len(created)} file link(s) on work package #{input.work_package_id}."
        )

    except Exception as e:
        if "404" in str(e):
            return format_error(
                "Storage or work package not found. Verify the storage is linked "
                "to the project (see list_project_storages)."
            )
        return format_error(f"Failed to create file links: {e!s}")


@mcp.tool(
    tags={"write", "content", "situational", "situational-write", "delete_file_link"}
)
async def delete_file_link(file_link_id: int) -> str:
    """Delete a file link from a work package.

    This removes the link between the work package and the file. The file
    itself is not deleted from the storage.

    Args:
        file_link_id: The file link ID to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_file_link(file_link_id)
        return format_success(f"File link #{file_link_id} deleted.")

    except Exception as e:
        return format_error(f"Failed to delete file link #{file_link_id}: {e!s}")
