#!/usr/bin/env python3
"""One-time setup script: provision the integration test project on a live OpenProject instance.

Creates everything that can be done via API. Prints a checklist of remaining
click-ops steps that cannot be automated.

Usage:
    uv run python scripts/setup_test_project.py

Required env vars:
    OPENPROJECT_URL       e.g. https://openproject.thomasgerke.com
    OPENPROJECT_API_KEY   admin API token

Optional env vars:
    OPENPROJECT_PROJECT   project identifier slug (default: mcp-test)
    OPENPROJECT_CA_BUNDLE path to PEM bundle for private CAs

Run this script once before running the integration test suite. It is
idempotent — re-running it is safe.
"""

import asyncio
import os
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


async def find_membership(
    client: OpenProjectClient, project_id: int, user_id: int
) -> dict | None:
    result = await client.get_memberships(project_id=project_id)
    for m in result.get("_embedded", {}).get("elements", []):
        href = m.get("_links", {}).get("principal", {}).get("href", "")
        if href.endswith(f"/{user_id}"):
            return m
    return None


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
    my_id = me.get("id")
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
                "description": "Dedicated project for openproject-mcp-server integration tests. Safe to delete.",
                "public": False,
            }
        )
        project_id = int(created["id"])
        ok(f"created project '{project_slug}' (id={project_id})")

    # ── 2. Work package types ─────────────────────────────────────────────────
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
    section("Seed work package (WP #46 equivalent)")
    import json as _json

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

    print(
        f"\n  {BOLD}→ Set OPENPROJECT_SEED_WP_ID={seed_wp_id} when running tests{RESET}"
    )

    # ── 4. Member ─────────────────────────────────────────────────────────────
    section("Project membership")
    existing_membership = await find_membership(client, project_id, my_id)
    if existing_membership:
        roles = [
            r.get("title")
            for r in existing_membership.get("_links", {}).get("roles", [])
        ]
        skip(f"already a member with roles: {roles}")
    else:
        # Find the 'Member' role (or 'Project admin' as fallback)
        roles_result = await client.get_roles()
        all_roles = roles_result.get("_embedded", {}).get("elements", [])
        system_names = {"anonymous", "non member", "non-member"}
        assignable_roles = [
            r for r in all_roles if r.get("name", "").lower() not in system_names
        ]
        member_role = next(
            (r for r in assignable_roles if r.get("name", "").lower() == "member"),
            assignable_roles[0] if assignable_roles else None,
        )
        if not member_role:
            fail("no assignable roles found — cannot create membership")
        else:
            try:
                created_m = await client.create_membership(
                    {
                        "project_id": project_id,
                        "user_id": my_id,
                        "role_ids": [member_role["id"]],
                    }
                )
                ok(
                    f"added as '{member_role['name']}' (membership id={created_m.get('id')})"
                )
            except Exception as e:
                fail(f"create membership: {e}")

    # ── 5. Version ────────────────────────────────────────────────────────────
    section("Version (for CF13 / version-type custom fields)")
    await find_or_create_version(client, project_id, "v1.0-test")

    # ── 6. Query ──────────────────────────────────────────────────────────────
    section("Saved query (smoke-test for query tools)")
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

    # ── 7. Custom action ──────────────────────────────────────────────────────
    section("Custom action")
    try:
        action = await client.get_custom_action(1)
        ok(f"custom action id=1 exists: '{action.get('name')}'")
    except Exception:
        fail(
            "custom action id=1 not found — must be created via click-ops "
            "(see 'Click-ops checklist' below)"
        )

    # ── 8. Print env block ────────────────────────────────────────────────────
    section("Environment variables for test run")
    print(f"""
  Copy this block to your shell before running the integration tests:

  export OPENPROJECT_URL="{url}"
  export OPENPROJECT_API_KEY="<your-token>"
  export OPENPROJECT_PROJECT="{project_slug}"
  export OPENPROJECT_SEED_WP_ID="{seed_wp_id}"
""")

    # ── 9. Click-ops checklist ────────────────────────────────────────────────
    heading("Click-ops checklist (cannot be automated)")
    print(
        "  These steps require the OpenProject web UI. Do them once after running\n"
        "  this script. Check each one off before running the integration suite.\n"
    )

    clickops = [
        (
            "Enable modules on the test project",
            f"Projects → {project_slug} → Settings → Modules\n"
            "    ☐ Work packages (required — enables WP tracking)\n"
            "    ☐ Time and costs (required for test_costs + test_time_entries)\n"
            "    ☐ Wiki (required for test_wiki)\n"
            "    ☐ News (required for test_news)\n"
            "    ☐ Boards / Backlogs (optional — not tested)\n"
            f"    Then set env var: OPENPROJECT_MODULE_TIME_COSTS=1",
        ),
        (
            "Enable custom fields on the test project",
            f"Projects → {project_slug} → Settings → Custom fields\n"
            "    Check each custom field in the list below. Create them first\n"
            "    in Administration → Custom fields → Work packages if missing:\n"
            "    ☐ CF2 / jira_key     — Text (String)     — types: Task\n"
            "    ☐ CF3 / trigger      — Long text          — types: Task\n"
            "    ☐ CF4 / test_bool    — Boolean            — types: Task\n"
            "    ☐ CF5 / test_date    — Date               — types: Task\n"
            "    ☐ CF6 / test_float   — Float              — types: Task\n"
            "    ☐ CF8 / test_int     — Integer            — types: Task\n"
            "    ☐ CF9 / test_link    — URL                — types: Task\n"
            "    ☐ CF11 / test_text   — Text (String)      — types: Task\n"
            "    ☐ CF15 / test_longtext — Long text        — types: Task",
        ),
        (
            "Create the 'Start work' custom action",
            "Administration → Work packages → Custom actions → + Custom action\n"
            "    Name:       Start work\n"
            "    Condition:  Status = New\n"
            "    Action:     Status → In Progress\n"
            "    Note the ID from the URL (/admin/custom_actions/<ID>/edit)\n"
            "    Then set: OPENPROJECT_CUSTOM_ACTION_ID=<ID>",
        ),
        (
            "Configure time entry activities",
            "Administration → Time and costs → Activities\n"
            "    Create at least one activity (e.g. 'Development')\n"
            "    Required for test_time_entries and test_costs",
        ),
        (
            "Create a cost type",
            "Administration → Cost types → + Cost type\n"
            "    Create at least one cost type (e.g. 'Consulting', unit=hour)\n"
            "    Required for test_costs",
        ),
        (
            "Grant 'edit journals' permission (for test_get_and_update_activity)",
            "Administration → Roles and permissions → Member\n"
            "    Work packages section → check 'Edit work package journals'\n"
            "    Without this, update_activity returns 400",
        ),
        (
            "Configure attachments storage (for test_attachment_lifecycle)",
            "Administration → Attachments\n"
            "    Verify 'Attachment storage' path is writable by the app user.\n"
            "    The upload endpoint currently returns 500 — check server logs.",
        ),
    ]

    for i, (title, detail) in enumerate(clickops, 1):
        print(f"  {BOLD}{i}. {title}{RESET}")
        for line in detail.split("\n"):
            print(f"     {line}")
        print()

    # ── 10. Run command ───────────────────────────────────────────────────────
    heading("Run the integration tests")
    print(f"""  # Minimum (no optional modules):
  uv run pytest tests/integration -m integration -v

  # With Time and costs module enabled:
  OPENPROJECT_MODULE_TIME_COSTS=1 \\
  OPENPROJECT_SEED_WP_ID={seed_wp_id} \\
  uv run pytest tests/integration -m integration -v

  # Run a single module:
  uv run pytest tests/integration/test_versions.py -m integration -v

  # See all available markers:
  uv run pytest tests/integration --markers
""")

    print(
        f"{GREEN}{BOLD}Setup complete.{RESET} Work through the click-ops checklist above, then run the tests.\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
