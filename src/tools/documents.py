"""Document management tools.

Note: Documents cannot be created via the v3 API (no POST /documents endpoint).
Existing documents can be listed, retrieved, and their metadata updated.
"""

from pydantic import BaseModel, Field

from src.server import get_client
from src.tool_registry import tracked_tool
from src.utils.formatting import format_error, format_success


class UpdateDocumentInput(BaseModel):
    document_id: int = Field(..., description="Document ID to update", gt=0)
    title: str | None = Field(None, description="New document title")
    description: str | None = Field(None, description="New description (markdown)")


@tracked_tool(tags={"read", "documents", "documents-read", "list_documents"})
async def list_documents() -> str:
    """List all documents in OpenProject.

    Note: Documents cannot be created via the v3 API — only listed, retrieved,
    and metadata-updated. Creation is done through the web UI.

    Returns:
        List of documents with their titles and IDs
    """
    try:
        client = get_client()
        result = await client.get_documents()
        docs = result.get("_embedded", {}).get("elements", [])

        if not docs:
            return "No documents found."

        text = f"✅ **Documents ({len(docs)}):**\n\n"
        for d in docs:
            text += f"- **{d.get('title', 'Untitled')}** (ID: {d.get('id', 'N/A')})\n"
            if d.get("description", {}).get("raw"):
                desc = d["description"]["raw"][:80]
                text += (
                    f"  {desc}{'...' if len(d['description']['raw']) > 80 else ''}\n"
                )
        return text

    except Exception as e:
        return format_error(f"Failed to list documents: {e!s}")


@tracked_tool(tags={"read", "documents", "documents-read", "get_document"})
async def get_document(document_id: int) -> str:
    """Get details of a specific document.

    Args:
        document_id: The document ID

    Returns:
        Document title, description, and metadata
    """
    try:
        client = get_client()
        d = await client.get_document(document_id)

        text = f"✅ **Document #{d.get('id', document_id)}:**\n\n"
        text += f"**Title**: {d.get('title', 'N/A')}\n"
        if d.get("description", {}).get("raw"):
            text += f"**Description**: {d['description']['raw']}\n"
        if d.get("createdAt"):
            text += f"**Created**: {d['createdAt']}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get document #{document_id}: {e!s}")


@tracked_tool(tags={"write", "documents", "documents-write", "update_document"})
async def update_document(input: UpdateDocumentInput) -> str:
    """Update a document's title or description.

    Args:
        input: Document ID and optional title/description to update

    Returns:
        Success message with updated document details
    """
    try:
        data = {}
        if input.title is not None:
            data["title"] = input.title
        if input.description is not None:
            data["description"] = input.description
        if not data:
            return format_error("No fields provided to update.")

        client = get_client()
        d = await client.update_document(input.document_id, data)
        text = format_success(f"Document #{input.document_id} updated.\n\n")
        text += f"**Title**: {d.get('title', 'N/A')}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to update document #{input.document_id}: {e!s}")
