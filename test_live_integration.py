#!/usr/bin/env python3
"""
Live integration tests for new API domains.

Pulls credentials from Infisical at runtime. Requires:
  - infisical CLI authenticated
  - OPENPROJECT_URL env var OR fallback to discovering it from Infisical

Tests each new endpoint with real HTTP calls. Each test is self-contained
and cleans up after itself where possible.

Usage:
    OPENPROJECT_URL=https://your-instance uv run python test_live_integration.py
"""

import asyncio
import subprocess
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INFISICAL_PROJECT_ID = "62dc8b3e-db71-4cb3-aa1f-aa457d665edb"
INFISICAL_ENV = "prod"

# ──────────────────────────────────────────────
# Credential helpers
# ──────────────────────────────────────────────

def _infisical_get(key: str) -> str:
    result = subprocess.run(
        [
            "infisical", "secrets", "get", key,
            "--projectId", INFISICAL_PROJECT_ID,
            "--env", INFISICAL_ENV,
            "--plain",
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"infisical get {key} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def load_credentials() -> tuple[str, str]:
    """Return (base_url, api_key). Reads key from Infisical."""
    base_url = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
    if not base_url:
        raise RuntimeError(
            "Set OPENPROJECT_URL env var (e.g. https://openproject.yourdomain.com)"
        )
    api_key = _infisical_get("openproject-api-token-tom")
    return base_url, api_key


# ──────────────────────────────────────────────
# Test runner helpers
# ──────────────────────────────────────────────

PASS = "✅"
FAIL = "❌"
results: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"{status} {name}" + (f": {detail}" if detail else ""))


async def run_tests(base_url: str, api_key: str):
    from src.client import OpenProjectClient
    client = OpenProjectClient(base_url=base_url, api_key=api_key)

    # ── helper: find a real project to test against ──
    projects_resp = await client.get_projects()
    projects = projects_resp.get("_embedded", {}).get("elements", [])
    if not projects:
        print("No projects found — cannot run integration tests")
        sys.exit(1)
    project = projects[0]
    project_id = project["id"]
    project_name = project.get("name", "unknown")
    print(f"\nUsing project: {project_name} (ID: {project_id})\n")

    # ════════════════════════════════════════════
    # WIKI
    # ════════════════════════════════════════════
    print("─── Wiki ───────────────────────────────────")

    # list wiki pages
    try:
        resp = await client.get_wiki_pages(project_id)
        pages = resp.get("_embedded", {}).get("elements", [])
        record("get_wiki_pages", True, f"{len(pages)} pages found")
    except Exception as e:
        record("get_wiki_pages", False, str(e))
        pages = []

    # upsert a test page
    test_slug = "claude-integration-test"
    try:
        resp = await client.upsert_wiki_page(
            project_id, test_slug,
            {"title": "Claude Integration Test", "content": "# Test\n\nAuto-created by live integration test."}
        )
        record("upsert_wiki_page (create)", True, f"slug={resp.get('slug', test_slug)}")
        created_slug = resp.get("slug", test_slug)
    except Exception as e:
        record("upsert_wiki_page (create)", False, str(e))
        created_slug = test_slug

    # get the page back
    try:
        resp = await client.get_wiki_page(project_id, created_slug)
        content_raw = resp.get("content", {}).get("raw", "") if isinstance(resp.get("content"), dict) else ""
        record("get_wiki_page", "# Test" in content_raw, f"title={resp.get('title', '?')}")
    except Exception as e:
        record("get_wiki_page", False, str(e))

    # update it
    try:
        resp = await client.upsert_wiki_page(
            project_id, created_slug,
            {"title": "Claude Integration Test (updated)", "content": "# Test\n\nUpdated content."}
        )
        record("upsert_wiki_page (update)", True, f"title={resp.get('title', '?')}")
    except Exception as e:
        record("upsert_wiki_page (update)", False, str(e))

    # delete it
    try:
        await client.delete_wiki_page(project_id, created_slug)
        record("delete_wiki_page", True)
    except Exception as e:
        record("delete_wiki_page", False, str(e))

    # ════════════════════════════════════════════
    # GROUPS
    # ════════════════════════════════════════════
    print("\n─── Groups ─────────────────────────────────")

    try:
        resp = await client.get_groups()
        groups = resp.get("_embedded", {}).get("elements", [])
        record("get_groups", True, f"{len(groups)} groups found")
    except Exception as e:
        record("get_groups", False, str(e))
        groups = []

    if groups:
        group_id = groups[0]["id"]
        try:
            resp = await client.get_group(group_id)
            record("get_group", resp.get("id") == group_id, f"name={resp.get('name', '?')}")
        except Exception as e:
            record("get_group", False, str(e))

    # ════════════════════════════════════════════
    # NOTIFICATIONS
    # ════════════════════════════════════════════
    print("\n─── Notifications ──────────────────────────")

    try:
        resp = await client.get_notifications(page_size=5)
        items = resp.get("_embedded", {}).get("elements", [])
        total = resp.get("total", len(items))
        record("get_notifications", True, f"{total} total notifications")
    except Exception as e:
        record("get_notifications", False, str(e))
        items = []

    # mark_all_notifications_read (safe — just marks inbox)
    try:
        await client.mark_all_notifications_read()
        record("mark_all_notifications_read", True)
    except Exception as e:
        record("mark_all_notifications_read", False, str(e))

    # ════════════════════════════════════════════
    # ATTACHMENTS
    # ════════════════════════════════════════════
    print("\n─── Attachments ────────────────────────────")

    # Get a work package to attach to
    wp_resp = await client.get_work_packages(project_id=project_id, page_size=1)
    wps = wp_resp.get("_embedded", {}).get("elements", [])
    if wps:
        wp_id = wps[0]["id"]
        wp_subject = wps[0].get("subject", "?")
        print(f"  Using WP #{wp_id}: {wp_subject}")

        # list attachments (before)
        try:
            resp = await client.list_attachments("work_packages", wp_id)
            before_count = len(resp.get("_embedded", {}).get("elements", []))
            record("list_attachments", True, f"{before_count} existing attachments")
        except Exception as e:
            record("list_attachments", False, str(e))
            before_count = 0

        # upload a small text attachment
        test_content = b"Claude live integration test attachment"
        try:
            resp = await client.upload_attachment(
                container_type="work_packages",
                container_id=wp_id,
                file_bytes=test_content,
                filename="claude-test.txt",
                content_type="text/plain",
            )
            att_id = resp.get("id")
            record("upload_attachment", att_id is not None, f"id={att_id}")
        except Exception as e:
            record("upload_attachment", False, str(e))
            att_id = None

        # get attachment metadata
        if att_id:
            try:
                resp = await client.get_attachment(att_id)
                record("get_attachment", resp.get("id") == att_id, f"fileName={resp.get('fileName', '?')}")
            except Exception as e:
                record("get_attachment", False, str(e))

            # delete it
            try:
                await client.delete_attachment(att_id)
                record("delete_attachment", True)
            except Exception as e:
                record("delete_attachment", False, str(e))
    else:
        print("  No work packages found — skipping attachment tests")

    # ════════════════════════════════════════════
    # COST TYPES + ENTRIES
    # ════════════════════════════════════════════
    print("\n─── Cost types & entries ───────────────────")

    try:
        resp = await client.get_cost_types()
        cost_types = resp.get("_embedded", {}).get("elements", [])
        record("get_cost_types", True, f"{len(cost_types)} types found")
    except Exception as e:
        record("get_cost_types", False, str(e))
        cost_types = []

    if cost_types and wps:
        cost_type_id = cost_types[0]["id"]
        cost_type_name = cost_types[0].get("name", "?")
        print(f"  Using cost type: {cost_type_name} (ID: {cost_type_id})")

        # create a cost entry
        try:
            resp = await client.create_cost_entry({
                "project_id": project_id,
                "work_package_id": wp_id,
                "cost_type_id": cost_type_id,
                "units": 100.0,
                "spent_on": "2026-06-18",
                "comment": "Claude live integration test",
            })
            entry_id = resp.get("id")
            record("create_cost_entry", entry_id is not None, f"id={entry_id}")
        except Exception as e:
            record("create_cost_entry", False, str(e))
            entry_id = None

        # list cost entries
        try:
            resp = await client.get_cost_entries(work_package_id=wp_id)
            entries = resp.get("_embedded", {}).get("elements", [])
            record("get_cost_entries", True, f"{len(entries)} entries for WP #{wp_id}")
        except Exception as e:
            record("get_cost_entries", False, str(e))

        # update it
        if entry_id:
            try:
                resp = await client.update_cost_entry(entry_id, {
                    "units": 200.0,
                    "comment": "Claude live integration test (updated)",
                })
                record("update_cost_entry", True, f"units={resp.get('units', '?')}")
            except Exception as e:
                record("update_cost_entry", False, str(e))

            # delete it
            try:
                await client.delete_cost_entry(entry_id)
                record("delete_cost_entry", True)
            except Exception as e:
                record("delete_cost_entry", False, str(e))
    elif not cost_types:
        print("  No cost types found — Costs module may not be enabled; skipping cost entry tests")
    elif not wps:
        print("  No work packages — skipping cost entry tests")


async def main():
    print("=" * 60)
    print("OpenProject Live Integration Tests")
    print("New API domains: wiki, groups, notifications, attachments, costs")
    print("=" * 60)

    try:
        base_url, api_key = load_credentials()
    except Exception as e:
        print(f"\n{FAIL} Could not load credentials: {e}")
        sys.exit(1)

    print(f"\nConnecting to: {base_url}")

    await run_tests(base_url, api_key)

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    skipped = [n for n, ok, d in results if not ok and "skip" in d.lower()]
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")
    if failed:
        print("\nFailed tests:")
        for name, ok, detail in results:
            if not ok:
                print(f"  {FAIL} {name}: {detail}")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
