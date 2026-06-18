"""Wiki page management tools for OpenProject."""

from typing import Optional
from pydantic import BaseModel, Field

from src.server import mcp, get_client
from src.utils.formatting import (
    format_wiki_page_list,
    format_wiki_page_detail,
    format_success,
    format_error,
)


class UpsertWikiPageInput(BaseModel):
    project_id: int = Field(..., description="Project ID", gt=0)
    slug: str = Field(..., description="URL slug (e.g. 'getting-started')", min_length=1)
    title: str = Field(..., description="Page title", min_length=1, max_length=255)
    content: str = Field(..., description="Page body (Markdown)")
    parent_slug: Optional[str] = Field(None, description="Slug of parent page (for nesting)")


@mcp.tool
async def list_wiki_pages(project_id: int) -> str:
    """List all wiki pages for a project.

    Args:
        project_id: The project ID

    Returns:
        List of wiki pages with slugs and last-updated dates
    """
    try:
        client = get_client()
        result = await client.get_wiki_pages(project_id)
        pages = result.get("_embedded", {}).get("elements", [])
        return format_wiki_page_list(pages)
    except Exception as e:
        return format_error(f"Failed to list wiki pages: {str(e)}")


@mcp.tool
async def get_wiki_page(project_id: int, slug: str) -> str:
    """Get a single wiki page by slug, including full Markdown content.

    Args:
        project_id: The project ID
        slug: Page slug (from list_wiki_pages)

    Returns:
        Full wiki page content in Markdown
    """
    try:
        client = get_client()
        page = await client.get_wiki_page(project_id, slug)
        return format_wiki_page_detail(page)
    except Exception as e:
        return format_error(f"Failed to get wiki page: {str(e)}")


@mcp.tool
async def upsert_wiki_page(input: UpsertWikiPageInput) -> str:
    """Create or update a wiki page (idempotent — safe to call on existing pages).

    The slug uniquely identifies the page within a project. If a page with
    that slug exists it is updated; otherwise it is created.

    Args:
        input: Page data including project_id, slug, title, content (Markdown),
               and optional parent_slug for nested pages

    Returns:
        Success message with page details

    Example:
        {
            "project_id": 3,
            "slug": "onboarding",
            "title": "Onboarding Guide",
            "content": "# Onboarding\\n\\nWelcome to the team."
        }
    """
    try:
        client = get_client()
        data = {"title": input.title, "content": input.content}
        if input.parent_slug:
            data["parent_slug"] = input.parent_slug
        page = await client.upsert_wiki_page(input.project_id, input.slug, data)
        result = format_success(f"Wiki page '{page.get('title', input.title)}' saved.")
        result += f"\n\n**Slug**: `{page.get('slug', input.slug)}`"
        result += f"\n**Project**: {input.project_id}"
        return result
    except Exception as e:
        return format_error(f"Failed to save wiki page: {str(e)}")


@mcp.tool
async def delete_wiki_page(project_id: int, slug: str) -> str:
    """Delete a wiki page permanently.

    WARNING: Cannot be undone.

    Args:
        project_id: The project ID
        slug: Page slug to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()
        await client.delete_wiki_page(project_id, slug)
        return format_success(f"Wiki page '{slug}' in project #{project_id} deleted.")
    except Exception as e:
        return format_error(f"Failed to delete wiki page: {str(e)}")
