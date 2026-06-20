"""Response formatting utilities for consistent output across all tools."""

__all__ = [
    "format_error",
    "format_success",
    "format_project_list",
    "format_work_package_list",
    "format_news_list",
    "format_news_detail",
    "format_wiki_page_detail",
]


def format_project_list(projects: list[dict]) -> str:
    """Format project list with consistent styling.

    Args:
        projects: List of project dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not projects:
        return "No projects found."

    text = f"✅ Found {len(projects)} project(s):\n\n"
    for project in projects:
        text += f"- **{project.get('name', 'Unnamed')}** (ID: {project.get('id')})\n"
        text += f"  Status: {'Active' if project.get('active') else 'Inactive'}\n"
        if project.get("description"):
            desc = project.get("description", {})
            if isinstance(desc, dict):
                desc_text = desc.get("raw", "")[:100]
            else:
                desc_text = str(desc)[:100]
            if desc_text:
                text += f"  Description: {desc_text}...\n"
        text += "\n"
    return text


def format_work_package_list(
    work_packages: list[dict],
    show_days_overdue: bool = False,
    show_days_until: bool = False,
) -> str:
    """Format work package list with embedded data and prominent status display.

    Args:
        work_packages: List of work package dictionaries from API
        show_days_overdue: If True, show how many days overdue each task is (for overdue filter)
        show_days_until: If True, show how many days until due (for due soon filter)

    Returns:
        Formatted markdown string with enhanced status visibility
    """
    if not work_packages:
        return "No work packages found."

    text = f"✅ Found {len(work_packages)} work package(s):\n\n"
    for wp in work_packages:
        wp_id = wp.get("id", "N/A")
        subject = wp.get("subject", "No title")

        # Extract data from both _embedded and _links (OpenProject uses both)
        embedded = wp.get("_embedded", {})
        links = wp.get("_links", {})

        # Get status - try _embedded first, then _links as fallback
        status_data = embedded.get("status", {})
        if not status_data or not status_data.get("name"):
            # Fallback: try getting from _links
            status_link = links.get("status", {})
            status_name = status_link.get("title", "Unknown")
            is_closed = "closed" in status_name.lower() or "done" in status_name.lower()
        else:
            status_name = status_data.get("name", "Unknown")
            is_closed = status_data.get("isClosed", False)

        # Status emoji indicator
        if is_closed:
            status_emoji = "✅"
            status_label = f"{status_name} (CLOSED)"
        elif "progress" in status_name.lower():
            status_emoji = "🔄"
            status_label = status_name
        elif "blocked" in status_name.lower():
            status_emoji = "🚫"
            status_label = status_name
        elif "new" in status_name.lower() or "open" in status_name.lower():
            status_emoji = "📋"
            status_label = status_name
        else:
            status_emoji = "⚪"
            status_label = status_name

        # Main entry with prominent status
        text += f"### {status_emoji} #{wp_id}: {subject}\n"
        text += f"**Status**: {status_label}\n"

        # Type - try _embedded first, then _links
        type_data = embedded.get("type", {})
        if type_data and type_data.get("name"):
            text += f"  Type: {type_data.get('name')}\n"
        elif "type" in links:
            type_name = links["type"].get("title", "Unknown")
            text += f"  Type: {type_name}\n"

        # Priority - try _embedded first, then _links
        priority_data = embedded.get("priority", {})
        if priority_data and priority_data.get("name"):
            priority_name = priority_data.get("name", "Unknown")
        elif "priority" in links:
            priority_name = links["priority"].get("title", "Unknown")
        else:
            priority_name = None

        if priority_name:
            # Add priority emoji
            if (
                "immediate" in priority_name.lower()
                or "urgent" in priority_name.lower()
            ):
                priority_display = f"🔴 {priority_name}"
            elif "high" in priority_name.lower():
                priority_display = f"🟠 {priority_name}"
            elif "low" in priority_name.lower():
                priority_display = f"🟢 {priority_name}"
            else:
                priority_display = priority_name
            text += f"  Priority: {priority_display}\n"

        # Assignee is in _links
        assignee_link = links.get("assignee")
        if assignee_link:
            assignee_name = assignee_link.get("title", "Unknown")
            text += f"  Assignee: {assignee_name}\n"
        else:
            text += "  Assignee: Unassigned\n"

        # Date fields with enhanced display for overdue/due soon
        if wp.get("startDate"):
            text += f"  Start: {wp['startDate']}\n"
        if wp.get("dueDate"):
            due_date = wp["dueDate"]

            # Show days overdue if requested
            if show_days_overdue and "_days_overdue" in wp:
                days = wp["_days_overdue"]
                if days == 1:
                    text += f"  Due: {due_date} ⚠️ **{days} day overdue**\n"
                else:
                    text += f"  Due: {due_date} ⚠️ **{days} days overdue**\n"
            # Show days until if requested
            elif show_days_until and "_days_until" in wp:
                days = wp["_days_until"]
                if days == 0:
                    text += f"  Due: {due_date} 🔴 **Due today!**\n"
                elif days == 1:
                    text += f"  Due: {due_date} 🟠 **Due tomorrow**\n"
                else:
                    text += f"  Due: {due_date} ⏰ **Due in {days} days**\n"
            else:
                text += f"  Due: {due_date}\n"

        text += "\n"
    return text


def format_error(error_message: str) -> str:
    """Format error message consistently.

    Args:
        error_message: Error message string

    Returns:
        Formatted error string with ❌ prefix
    """
    return f"❌ Error: {error_message}"


def format_success(message: str) -> str:
    """Format success message consistently.

    Args:
        message: Success message string

    Returns:
        Formatted success string with ✅ prefix
    """
    return f"✅ {message}"


def format_news_list(news_items: list[dict]) -> str:
    """Format news list with project, author, and dates.

    Args:
        news_items: List of news dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not news_items:
        return "No news entries found."

    text = f"📰 News List ({len(news_items)} item{'s' if len(news_items) != 1 else ''}):\n\n"

    for news in news_items:
        news_id = news.get("id", "N/A")
        title = news.get("title", "No title")
        summary = news.get("summary", "")
        created_at = news.get("createdAt", "Unknown")

        # Format date to be more readable (YYYY-MM-DD)
        if created_at and created_at != "Unknown":
            try:
                created_date = created_at.split("T")[0]
            except Exception:
                created_date = created_at
        else:
            created_date = created_at

        # Extract project and author from _links
        links = news.get("_links", {})
        project_name = links.get("project", {}).get("title", "Unknown Project")
        author_name = links.get("author", {}).get("title", "Unknown Author")

        # Build formatted entry
        text += f"**{news_id}. {title}**\n"
        text += f"   📁 Project: {project_name}\n"
        text += f"   👤 Author: {author_name}\n"
        text += f"   📅 Created: {created_date}\n"

        if summary:
            # Truncate summary if too long
            summary_preview = summary[:150] + "..." if len(summary) > 150 else summary
            text += f"   📝 {summary_preview}\n"

        text += "\n"

    return text


def format_news_detail(news_item: dict) -> str:
    """Format detailed news entry with full content.

    Args:
        news_item: News dictionary from API

    Returns:
        Formatted markdown string
    """
    text = f"📰 News Entry #{news_item.get('id')}\n\n"

    # Title
    title = news_item.get("title", "No title")
    text += f"# {title}\n\n"

    # Metadata
    links = news_item.get("_links", {})
    project_name = links.get("project", {}).get("title", "Unknown Project")
    author_name = links.get("author", {}).get("title", "Unknown Author")
    created_at = news_item.get("createdAt", "Unknown")

    # Format date
    if created_at and created_at != "Unknown":
        try:
            created_date = created_at.split("T")[0]
            created_time = (
                created_at.split("T")[1].split(".")[0] if "T" in created_at else ""
            )
            created_display = f"{created_date} {created_time}"
        except Exception:
            created_display = created_at
    else:
        created_display = created_at

    text += f"**Project**: {project_name}\n"
    text += f"**Author**: {author_name}\n"
    text += f"**Created**: {created_display}\n\n"

    # Summary
    summary = news_item.get("summary", "")
    if summary:
        text += f"## Summary\n\n{summary}\n\n"

    # Description (full content with markdown)
    description = news_item.get("description", {})
    if description:
        if isinstance(description, dict):
            desc_text = description.get("raw", "")
        else:
            desc_text = str(description)

        if desc_text:
            text += f"## Description\n\n{desc_text}\n\n"

    # Links section
    text += "---\n"
    text += "**Links**:\n"
    if "self" in links:
        text += f"- [View in OpenProject]({links['self'].get('href', '#')})\n"
    if "project" in links:
        text += f"- [Project]({links['project'].get('href', '#')})\n"

    return text


def format_wiki_page_detail(page: dict) -> str:
    """Format a single wiki page with full content."""
    title = page.get("title", "Untitled")
    slug = page.get("slug", page.get("id", "N/A"))
    updated = page.get("updatedAt", "")
    content_raw = (
        page.get("content", {}).get("raw", "")
        if isinstance(page.get("content"), dict)
        else ""
    )

    text = f"✅ **Wiki Page: {title}**\n\n"
    text += f"**Slug**: `{slug}`\n"
    if updated:
        text += f"**Updated**: {updated[:10]}\n"

    parent_links = page.get("_links", {}).get("parent", {})
    if parent_links and parent_links.get("href"):
        text += f"**Parent**: {parent_links.get('title', parent_links['href'])}\n"

    if content_raw:
        text += f"\n---\n{content_raw}\n"
    return text
