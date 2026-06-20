"""User and role management tools."""

from pydantic import BaseModel, Field

from src.server import get_client, mcp
from src.utils.formatting import format_error, format_success


class CreateUserInput(BaseModel):
    """Input for creating a new user."""

    login: str = Field(..., description="Unique login name")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    password: str | None = Field(
        None,
        description=(
            "Initial password. Some instances require this field; others don't. "
            "Even when set, the password may not enable basic-auth login on SSO-only "
            "instances — check your instance configuration."
        ),
    )
    admin: bool = Field(False, description="Grant administrator privileges")


class UpdateUserInput(BaseModel):
    """Input for updating an existing user."""

    user_id: int = Field(..., description="User ID to update", gt=0)
    first_name: str | None = Field(None, description="New first name")
    last_name: str | None = Field(None, description="New last name")
    email: str | None = Field(None, description="New email address")
    status: str | None = Field(
        None, description="New status: active, locked, registered"
    )
    admin: bool | None = Field(
        None, description="Set or revoke administrator privileges"
    )


class UpdateMyPreferencesInput(BaseModel):
    """Input for updating the authenticated user's preferences."""

    time_zone: str | None = Field(
        None, description="IANA timezone (e.g. 'America/New_York')"
    )
    wants_newsletters: bool | None = Field(None, description="Subscribe to newsletters")
    comment_sort_descending: bool | None = Field(
        None, description="Sort comments newest-first"
    )
    warn_on_leaving_unsaved: bool | None = Field(
        None, description="Warn before leaving unsaved changes"
    )
    auto_hide_popups: bool | None = Field(None, description="Auto-hide flash messages")
    pause_reminders: bool | None = Field(
        None, description="Pause all reminder notifications"
    )


@mcp.tool(tags={"read", "users", "core", "core-read", "list_users"})
async def list_users(name: str | None = None, status: str | None = None) -> str:
    """List users in OpenProject.

    Args:
        name: Optional name filter (searches for partial matches)
        status: Optional status filter (e.g., "active", "locked")

    Returns:
        List of users with their details
    """
    try:
        client = get_client()

        filters = []
        if name:
            filters.append({"name": {"operator": "~", "values": [name]}})
        if status:
            filters.append({"status": {"operator": "=", "values": [status]}})

        import json

        filters_json = json.dumps(filters) if filters else None

        result = await client.get_users(filters_json)
        users = result.get("_embedded", {}).get("elements", [])

        if not users:
            return "No users found."

        text = f"✅ **Found {len(users)} user(s):**\n\n"
        for user in users:
            text += (
                f"- **{user.get('name', 'Unknown')}** (ID: {user.get('id', 'N/A')})\n"
            )
            text += f"  Email: {user.get('email', 'N/A')}\n"
            text += f"  Login: {user.get('login', 'N/A')}\n"
            text += f"  Status: {user.get('status', 'N/A')}\n"
            if user.get("admin"):
                text += "  ✓ Administrator\n"
            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list users: {e!s}")


@mcp.tool(tags={"read", "users", "core", "core-read", "get_user"})
async def get_user(user_id: int) -> str:
    """Get detailed information about a specific user.

    Args:
        user_id: The user ID

    Returns:
        Detailed user information
    """
    try:
        client = get_client()
        user = await client.get_user(user_id)

        text = f"✅ **User #{user.get('id')}**\n\n"
        text += f"**Name**: {user.get('name', 'Unknown')}\n"
        text += f"**Email**: {user.get('email', 'N/A')}\n"
        text += f"**Login**: {user.get('login', 'N/A')}\n"
        text += f"**Status**: {user.get('status', 'N/A')}\n"
        text += f"**Admin**: {'Yes' if user.get('admin') else 'No'}\n"

        if user.get("createdAt"):
            text += f"**Created**: {user['createdAt']}\n"
        if user.get("updatedAt"):
            text += f"**Updated**: {user['updatedAt']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get user: {e!s}")


@mcp.tool(tags={"read", "users", "list_roles"})
async def list_roles() -> str:
    """List available user roles in OpenProject.

    Returns:
        List of roles with their permissions
    """
    try:
        client = get_client()

        result = await client.get_roles()
        roles = result.get("_embedded", {}).get("elements", [])

        if not roles:
            return "No roles found."

        text = "✅ **Available Roles:**\n\n"
        for role in roles:
            text += (
                f"- **{role.get('name', 'Unnamed')}** (ID: {role.get('id', 'N/A')})\n"
            )

        return text

    except Exception as e:
        return format_error(f"Failed to list roles: {e!s}")


@mcp.tool(tags={"read", "users", "get_role"})
async def get_role(role_id: int) -> str:
    """Get detailed information about a specific role.

    Args:
        role_id: The role ID

    Returns:
        Detailed role information including permissions
    """
    try:
        client = get_client()
        role = await client.get_role(role_id)

        text = f"✅ **Role #{role.get('id')}**\n\n"
        text += f"**Name**: {role.get('name', 'Unknown')}\n"

        # Add permissions if available
        if "_embedded" in role and "permissions" in role["_embedded"]:
            perms = role["_embedded"]["permissions"]
            if perms:
                text += f"\n**Permissions** ({len(perms)}):\n"
                for perm in perms[:10]:  # Show first 10
                    text += f"- {perm.get('name', 'Unknown')}\n"
                if len(perms) > 10:
                    text += f"... and {len(perms) - 10} more\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get role: {e!s}")


@mcp.tool(tags={"read", "users", "list_project_members"})
async def list_project_members(project_id: int) -> str:
    """List all members of a specific project.

    Args:
        project_id: The project ID

    Returns:
        List of project members with their roles
    """
    try:
        client = get_client()

        result = await client.get_memberships(project_id=project_id)
        memberships = result.get("_embedded", {}).get("elements", [])

        if not memberships:
            return f"No members found for project #{project_id}."

        text = f"✅ **Project #{project_id} Members ({len(memberships)}):**\n\n"
        for member in memberships:
            links = member.get("_links", {})

            # Get principal (user/group) information from _links
            principal_link = links.get("principal", {})
            name = principal_link.get("title", "Unknown")
            # Extract user ID from href: "/api/v3/users/7" -> 7
            principal_href = principal_link.get("href", "")
            user_id = principal_href.split("/")[-1] if principal_href else "N/A"

            text += f"- **{name}** (User ID: {user_id})\n"

            # Get roles from _links
            role_links = links.get("roles", [])
            if role_links:
                role_names = [r.get("title", "Unknown") for r in role_links]
                text += f"  Roles: {', '.join(role_names)}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list project members: {e!s}")


@mcp.tool(tags={"read", "users", "list_user_projects"})
async def list_user_projects(user_id: int) -> str:
    """List all projects a user is a member of.

    Args:
        user_id: The user ID

    Returns:
        List of projects the user belongs to
    """
    try:
        client = get_client()

        import json

        filters = json.dumps(
            [{"principal": {"operator": "=", "values": [str(user_id)]}}]
        )

        result = await client.get_memberships(filters)
        memberships = result.get("_embedded", {}).get("elements", [])

        if not memberships:
            return f"User #{user_id} is not a member of any projects."

        text = f"✅ **Projects for User #{user_id} ({len(memberships)}):**\n\n"
        for member in memberships:
            embedded = member.get("_embedded", {})

            if "project" in embedded:
                project_name = embedded["project"].get("name", "Unknown")
                text += f"- **{project_name}**\n"

            if "roles" in embedded:
                roles = [r.get("name", "Unknown") for r in embedded["roles"]]
                text += f"  Roles: {', '.join(roles)}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list user projects: {e!s}")


@mcp.tool(tags={"read", "users", "core", "core-read", "list_principals"})
async def list_principals(project_id: int | None = None) -> str:
    """List principals (users, groups, and placeholder users) in one call.

    More useful than separate list_users + list_groups calls when you need
    all assignable entities — e.g. when populating an assignee picker.

    Args:
        project_id: Optional project ID to filter to project members only

    Returns:
        List of principals with their type, ID, and name
    """
    try:
        client = get_client()
        result = await client.get_principals(project_id)
        principals = result.get("_embedded", {}).get("elements", [])

        if not principals:
            return "No principals found."

        text = f"✅ **Principals ({len(principals)}):**\n\n"
        for p in principals:
            ptype = p.get("_type", "Unknown")
            text += f"- **{p.get('name', 'Unknown')}** (ID: {p.get('id', 'N/A')}, type: {ptype})\n"
        return text

    except Exception as e:
        return format_error(f"Failed to list principals: {e!s}")


@mcp.tool(tags={"write", "users", "admin", "create_user"})
async def create_user(input: CreateUserInput) -> str:
    """Create a new user account (admin only).

    The account is created with 'active' status immediately. Some OpenProject
    instances require the `password` field; others do not (you'll get a 422 if
    yours does and you omit it). Even when a password is supplied, the user may
    still need to authenticate via SSO depending on your instance's auth configuration.

    Args:
        input: User details — login, first_name, last_name, email, and optional admin flag

    Returns:
        Success message with the new user ID and login
    """
    try:
        client = get_client()
        user = await client.create_user(
            {
                "login": input.login,
                "first_name": input.first_name,
                "last_name": input.last_name,
                "email": input.email,
                "admin": input.admin,
                "password": input.password,
            }
        )
        text = format_success("User created successfully.\n\n")
        text += f"**ID**: #{user.get('id', 'N/A')}\n"
        text += f"**Login**: {user.get('login', 'N/A')}\n"
        text += f"**Name**: {user.get('name', 'N/A')}\n"
        text += f"**Email**: {user.get('email', 'N/A')}\n"
        text += f"**Status**: {user.get('status', 'N/A')}\n"
        text += "\n⚠️ If no password was provided and your instance requires one, "
        text += "set it via Administration → Users → Edit before the user can log in."
        return text

    except Exception as e:
        if "403" in str(e):
            return format_error("create_user requires administrator privileges.")
        return format_error(f"Failed to create user: {e!s}")


@mcp.tool(tags={"write", "users", "admin", "update_user"})
async def update_user(input: UpdateUserInput) -> str:
    """Update an existing user account (admin only).

    Note: delete_user is not available via the OpenProject v3 API —
    it returns 403 even for system admins. Use lock/unlock (status change) instead.

    Args:
        input: User ID and optional fields to update

    Returns:
        Success message with updated user details
    """
    try:
        client = get_client()
        data: dict[str, object] = {}
        if input.first_name is not None:
            data["first_name"] = input.first_name
        if input.last_name is not None:
            data["last_name"] = input.last_name
        if input.email is not None:
            data["email"] = input.email
        if input.status is not None:
            data["status"] = input.status
        if input.admin is not None:
            data["admin"] = input.admin

        user = await client.update_user(input.user_id, data)
        text = format_success(f"User #{input.user_id} updated.\n\n")
        text += f"**Name**: {user.get('name', 'N/A')}\n"
        text += f"**Status**: {user.get('status', 'N/A')}\n"
        text += f"**Admin**: {'Yes' if user.get('admin') else 'No'}\n"
        return text

    except Exception as e:
        if "403" in str(e):
            return format_error("update_user requires administrator privileges.")
        return format_error(f"Failed to update user #{input.user_id}: {e!s}")


@mcp.tool(tags={"read", "users", "core", "core-read", "get_my_preferences"})
async def get_my_preferences() -> str:
    """Get the authenticated user's notification and UI preferences.

    Returns:
        Current preferences including timezone, reminder settings, and UI options
    """
    try:
        client = get_client()
        prefs = await client.get_my_preferences()

        text = "✅ **My Preferences:**\n\n"
        if prefs.get("timeZone"):
            text += f"**Time Zone**: {prefs['timeZone']}\n"
        text += f"**Comment sort**: {'Newest first' if prefs.get('commentSortDescending') else 'Oldest first'}\n"
        text += f"**Warn on unsaved**: {'Yes' if prefs.get('warnOnLeavingUnsaved') else 'No'}\n"
        text += (
            f"**Auto-hide popups**: {'Yes' if prefs.get('autoHidePopups') else 'No'}\n"
        )
        if prefs.get("pauseReminders"):
            text += "**Reminders**: Paused\n"
        if prefs.get("dailyReminders"):
            dr = prefs["dailyReminders"]
            if dr.get("enabled"):
                times = dr.get("times", [])
                text += f"**Daily reminders**: Enabled at {', '.join(times) if times else 'default time'}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to get preferences: {e!s}")


@mcp.tool(tags={"write", "users", "update_my_preferences"})
async def update_my_preferences(input: UpdateMyPreferencesInput) -> str:
    """Update the authenticated user's preferences.

    Only the fields you provide are updated; omitted fields are unchanged.

    Args:
        input: Preference fields to update (timezone, reminders, UI options)

    Returns:
        Success message with the updated preferences
    """
    try:
        client = get_client()
        data: dict = {}
        if input.time_zone is not None:
            data["timeZone"] = input.time_zone
        if input.wants_newsletters is not None:
            data["wantsNewsletters"] = input.wants_newsletters
        if input.comment_sort_descending is not None:
            data["commentSortDescending"] = input.comment_sort_descending
        if input.warn_on_leaving_unsaved is not None:
            data["warnOnLeavingUnsaved"] = input.warn_on_leaving_unsaved
        if input.auto_hide_popups is not None:
            data["autoHidePopups"] = input.auto_hide_popups
        if input.pause_reminders is not None:
            data["pauseReminders"] = input.pause_reminders

        prefs = await client.update_my_preferences(data)
        text = format_success("Preferences updated.\n\n")
        if prefs.get("timeZone"):
            text += f"**Time Zone**: {prefs['timeZone']}\n"
        if prefs.get("pauseReminders"):
            text += "**Reminders**: Paused\n"
        return text

    except Exception as e:
        return format_error(f"Failed to update preferences: {e!s}")
