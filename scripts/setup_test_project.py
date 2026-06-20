#!/usr/bin/env python3
"""One-time setup script: provision the integration test project on a live OpenProject instance.

Creates everything that can be automated via API, then prints a numbered
click-ops checklist for the remainder. Writes tests/integration/.env so
the test suite can be run without any manual env-var juggling.

Usage:
    uv run python scripts/setup_test_project.py

Required env vars:
    OPENPROJECT_URL       e.g. https://openproject.thomasgerke.com
    OPENPROJECT_API_KEY   admin API token

Optional env vars:
    OPENPROJECT_PROJECT   project identifier slug (default: mcp-test)
    OPENPROJECT_CA_BUNDLE path to PEM bundle for private CAs

Idempotent — safe to re-run at any time.
"""

import asyncio
import json as _json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client import OpenProjectClient

# ── colours ──────────────────────────────────────────────────────────────────

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def skip(msg: str) -> None:
    print(f"  {YELLOW}~{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}── {title} {'─' * max(0, 54 - len(title))}{RESET}")


def heading(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")


# ── helpers ───────────────────────────────────────────────────────────────────


async def find_project(client: OpenProjectClient, identifier: str) -> dict | None:
    result = await client.get_projects()
    for p in result.get("_embedded", {}).get("elements", []):
        if p.get("identifier") == identifier:
            return p
    return None


async def find_or_create_version(
    client: OpenProjectClient, project_id: int, name: str
) -> int:
    versions = (
        (await client.get_versions(project_id)).get("_embedded", {}).get("elements", [])
    )
    existing = next((v for v in versions if v.get("name") == name), None)
    if existing:
        skip(f"version '{name}' already exists (id={existing['id']})")
        return int(existing["id"])
    created = await client.create_version(project_id, {"name": name, "status": "open"})
    ok(f"created version '{name}' (id={created['id']})")
    return int(created["id"])


# ── main setup ────────────────────────────────────────────────────────────────


async def main() -> None:
    url = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
    key = os.environ.get("OPENPROJECT_API_KEY", "")
    project_slug = os.environ.get("OPENPROJECT_PROJECT", "mcp-test")

    if not url or not key:
        print("Error: OPENPROJECT_URL and OPENPROJECT_API_KEY must be set.")
        sys.exit(1)

    client = OpenProjectClient(base_url=url, api_key=key)

    print(f"\n{BOLD}OpenProject Integration Test Setup{RESET}")
    print(f"Instance: {url}")
    print(f"Project:  {project_slug}")

    # ── 0. Verify connection ──────────────────────────────────────────────────
    section("Connection")
    try:
        info = await client.test_connection()
        version = info.get("coreVersion") or info.get("instanceVersion") or "unknown"
        ok(f"connected (version {version})")
    except Exception as e:
        fail(f"cannot connect: {e}")
        sys.exit(1)

    me = await client.check_permissions()
    my_id = int(me.get("id"))
    my_name = me.get("name", "?")
    ok(f"authenticated as {my_name} (id={my_id})")

    # ── 1. Project ────────────────────────────────────────────────────────────
    section("Test project")
    project = await find_project(client, project_slug)
    if project:
        project_id = int(project["id"])
        skip(f"project '{project_slug}' already exists (id={project_id})")
    else:
        created = await client.create_project(
            {
                "name": "MCP Integration Tests",
                "identifier": project_slug,
                "description": (
                    "Dedicated project for openproject-mcp-server integration tests. "
                    "Safe to delete."
                ),
                "public": False,
            }
        )
        project_id = int(created["id"])
        ok(f"created project '{project_slug}' (id={project_id})")

    # ── 2. WP types ───────────────────────────────────────────────────────────
    section("WP types — discover available")
    types_result = await client.get_types(project_id)
    types = types_result.get("_embedded", {}).get("elements", [])
    if types:
        type_names = [f"{t['name']} (id={t['id']})" for t in types[:5]]
        ok(f"types enabled: {', '.join(type_names)}")
        first_type_id = int(types[0]["id"])
    else:
        fail("no WP types — enable at least 'Task' in Administration → Types")
        first_type_id = 1

    # ── 3. Seed work package ──────────────────────────────────────────────────
    section("Seed work package")
    filters = _json.dumps([{"project": {"operator": "=", "values": [str(project_id)]}}])
    wps = (
        (await client.get_work_packages(filters=filters))
        .get("_embedded", {})
        .get("elements", [])
    )
    seed_wp = next((w for w in wps if w.get("subject") == "mcp-test-seed"), None)
    if seed_wp:
        seed_wp_id = int(seed_wp["id"])
        skip(f"seed WP already exists (id={seed_wp_id})")
    else:
        created_wp = await client.create_work_package(
            {"project": project_id, "subject": "mcp-test-seed", "type": first_type_id}
        )
        seed_wp_id = int(created_wp["id"])
        ok(f"created seed WP (id={seed_wp_id})")

    # ── 4. Version ────────────────────────────────────────────────────────────
    section("Version (for version-type custom field tests)")
    await find_or_create_version(client, project_id, "v1.0-test")

    # ── 5. Saved query ────────────────────────────────────────────────────────
    section("Saved query")
    queries = (
        (await client.get_queries(project_id)).get("_embedded", {}).get("elements", [])
    )
    existing_q = next((q for q in queries if q.get("name") == "mcp-test-query"), None)
    if existing_q:
        skip(f"query 'mcp-test-query' already exists (id={existing_q['id']})")
    else:
        try:
            created_q = await client.create_query(
                {
                    "name": "mcp-test-query",
                    "_links": {"project": {"href": f"/api/v3/projects/{project_id}"}},
                }
            )
            ok(f"created query 'mcp-test-query' (id={created_q.get('id')})")
        except Exception as e:
            fail(f"create query: {e}")

    # ── 6. Bot user (for notification tests) ────────────────────────────────
    section("Bot user (mcp-test-bot)")
    users_result = await client.get_users()
    users = users_result.get("_embedded", {}).get("elements", [])
    bot_user = next((u for u in users if u.get("login") == "mcp-test-bot"), None)

    if bot_user:
        bot_id = int(bot_user["id"])
        skip(f"bot user already exists (id={bot_id}, status={bot_user.get('status')})")
        if bot_user.get("status") != "active":
            await client._request("PATCH", f"/users/{bot_id}", {"status": "active"})
            ok("restored bot to active")
    else:
        created_bot = await client._request(
            "POST",
            "/users",
            {
                "login": "mcp-test-bot",
                "firstName": "MCP",
                "lastName": "TestBot",
                "email": "mcp-test-bot@example.invalid",
                "admin": False,
                "status": "active",
                "password": "Mcp1Test!2Bot3",
            },
        )
        bot_id = int(created_bot["id"])
        ok(f"created bot user (id={bot_id})")

    # Ensure bot is a member of the test project (needed to create WPs)
    bot_membership = await client.get_memberships(project_id=project_id)
    bot_members = bot_membership.get("_embedded", {}).get("elements", [])
    bot_already_member = any(
        m.get("_links", {}).get("principal", {}).get("href", "").endswith(f"/{bot_id}")
        for m in bot_members
    )
    if bot_already_member:
        skip(f"bot is already a member of '{project_slug}'")
    else:
        # The API doesn't distinguish project roles from global roles — probe each
        roles_result = await client.get_roles()
        all_roles = roles_result.get("_embedded", {}).get("elements", [])
        system_names = {"anonymous", "non member", "non-member"}
        candidate_roles = [
            r for r in all_roles if r.get("name", "").lower() not in system_names
        ]
        added = False
        for role in candidate_roles:
            try:
                await client.create_membership(
                    {
                        "project_id": project_id,
                        "user_id": bot_id,
                        "role_ids": [role["id"]],
                    }
                )
                ok(f"added bot as '{role['name']}' in '{project_slug}'")
                added = True
                break
            except Exception as e:
                if "unassignable" in str(e).lower() or "422" in str(e):
                    continue
                fail(f"add bot membership: {e}")
                break
        if not added and not any("unassignable" in str(e) for e in []):
            fail("could not find an assignable project role for bot — add manually")

    # ── 7. Custom action probe ────────────────────────────────────────────────
    section("Custom action probe")
    custom_action_id_env = os.environ.get("OPENPROJECT_CUSTOM_ACTION_ID", "1")
    try:
        action = await client.get_custom_action(int(custom_action_id_env))
        ok(f"custom action id={custom_action_id_env} exists: '{action.get('name')}'")
    except Exception:
        fail(
            f"custom action id={custom_action_id_env} not found — "
            "see click-ops checklist item 3 below"
        )

    # ── 7. Write tests/integration/.env ──────────────────────────────────────
    section("Writing tests/integration/.env")
    env_path = pathlib.Path(__file__).parent.parent / "tests" / "integration" / ".env"
    env_content = (
        f"# Written by scripts/setup_test_project.py — gitignored, safe to re-generate\n"
        f"OPENPROJECT_URL={url}\n"
        f"OPENPROJECT_PROJECT={project_slug}\n"
        f"OPENPROJECT_SEED_WP_ID={seed_wp_id}\n"
        f"OPENPROJECT_CUSTOM_ACTION_ID={custom_action_id_env}\n"
        f"# Set API keys in your shell or here (never commit real tokens)\n"
        f"# OPENPROJECT_API_KEY=your-admin-token-here\n"
        f"# Bot token — log in as mcp-test-bot, go to User menu → Account settings\n"
        f"# → Access tokens → + API Token, paste value below:\n"
        f"# OPENPROJECT_BOT_API_KEY=mcp-test-bot-token-here\n"
        f"# Uncomment after enabling 'Time and costs' module on the project:\n"
        f"# OPENPROJECT_MODULE_TIME_COSTS=1\n"
    )
    env_path.write_text(env_content)
    ok(f"wrote {env_path}")
    print(
        f"\n  {YELLOW}Note:{RESET} OPENPROJECT_API_KEY is intentionally not written "
        f"to .env.\n  Set it in your shell before running tests.\n"
    )

    # ── 8. Click-ops checklist ────────────────────────────────────────────────
    heading("Click-ops checklist (cannot be automated)")
    print(
        "  These require the OpenProject web UI. Do them once and they persist.\n"
        "  Check each off before running the full integration suite.\n"
    )

    clickops = [
        (
            "Generate an API token for the bot user",
            "Log in as mcp-test-bot (password: Mcp1Test!2Bot3)\n"
            "    User menu (top right) → Account settings → Access tokens\n"
            "    → + API Token → copy the value\n"
            "    Paste it into tests/integration/.env as:\n"
            "    OPENPROJECT_BOT_API_KEY=<token>\n"
            "    This enables test_mark_single_notification_read: bot assigns a WP\n"
            "    to the admin user, which triggers a real notification.",
        ),
        (
            "Enable modules on the test project",
            f"Projects → {project_slug} → Settings → Modules\n"
            "    ☐ Work packages  (required)\n"
            "    ☐ Time and costs (required for test_costs + test_time_entries)\n"
            "    ☐ Wiki           (required for test_wiki)\n"
            "    ☐ News           (required for test_news)\n"
            f"\n    Then uncomment OPENPROJECT_MODULE_TIME_COSTS=1 in tests/integration/.env",
        ),
        (
            "Enable custom fields on the test project",
            f"Projects → {project_slug} → Settings → Custom fields\n"
            "    Create missing fields first in Administration → Custom fields → Work packages,\n"
            "    then enable each on this project. All apply to the Task type.\n"
            "    ☐ jira_key      — Text (String)\n"
            "    ☐ trigger       — Long text\n"
            "    ☐ test_bool     — Boolean\n"
            "    ☐ test_date     — Date\n"
            "    ☐ test_float    — Float\n"
            "    ☐ test_int      — Integer\n"
            "    ☐ test_link     — URL\n"
            "    ☐ test_text     — Text (String)\n"
            "    ☐ test_longtext — Long text",
        ),
        (
            "Create the 'Start work' custom action (if id=1 probe above failed)",
            "Administration → Work packages → Custom actions → + Custom action\n"
            "    Name:      Start work\n"
            "    Condition: Status = New\n"
            "    Action:    Status → In Progress\n"
            "    After saving, update OPENPROJECT_CUSTOM_ACTION_ID in tests/integration/.env\n"
            "    with the ID from the URL: /admin/custom_actions/<ID>/edit",
        ),
        (
            "Verify cost types exist (for test_costs)",
            "Administration → Cost types → ensure at least one type is configured\n"
            "    (e.g. 'Consulting', unit = hour). The test will skip if none exist.",
        ),
        (
            "Fix attachments storage (for test_attachment_lifecycle)",
            "The upload endpoint returns 500 on this instance.\n"
            "    Check: docker exec <container> ls -la /app/attachments\n"
            "    The directory must exist and be writable by the app user.",
        ),
    ]

    for i, (title, detail) in enumerate(clickops, 1):
        print(f"  {BOLD}{i}. {title}{RESET}")
        for line in detail.split("\n"):
            print(f"     {line}")
        print()

    # ── 9. Run commands ───────────────────────────────────────────────────────
    heading("Run the integration tests")
    print("""\
  export OPENPROJECT_API_KEY="<your-token>"

  # Core suite (no optional modules):
  uv run pytest tests/integration -m integration -v

  # Full suite (after enabling Time and costs on the project):
  uv run pytest tests/integration -m integration -v
  # (OPENPROJECT_MODULE_TIME_COSTS=1 is already in .env once you uncomment it)

  # Single module:
  uv run pytest tests/integration/test_versions.py -m integration -v

  # Available markers:
  uv run pytest tests/integration --markers
""")

    print(
        f"{GREEN}{BOLD}Setup complete.{RESET} Work through the click-ops checklist, then run the tests.\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
