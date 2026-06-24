# OpenProject MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server providing comprehensive integration with the [OpenProject](https://www.openproject.org/) API v3. Enables Claude and other MCP-compatible LLMs to read and manage projects, work packages, users, queries, file links, notifications, time entries, and more.

![status](https://img.shields.io/badge/status-stable-brightgreen) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Tests](https://img.shields.io/badge/tests-192%20unit%20%7C%2079%20integration-brightgreen)

---

## Tools summary

120 tools across 25 modules, tagged for granular access control.

| Module | Count | Key tools | Category tag |
|---|---|---|---|
| `work_packages` | 18 | list, search, create, update, delete, assign, comment, activities, types, statuses, priorities, overdue, due_soon, unassigned, recently_created, high_priority, nearly_complete | `work-packages` |
| `projects` | 7 | list, get, create[admin], update, delete[admin], add_subproject, get_subprojects | `projects` |
| `versions` | 4 | list, create, update, delete | `projects` |
| `hierarchy` | 3 | set_parent, remove_parent, list_children | `work-packages` |
| `relations` | 5 | list, get, create, update, delete | `work-packages` |
| `watchers` | 7 | list, available_watchers, add, remove, get_activity, update_activity, available_assignees | `work-packages` |
| `reminders` | 2 | list, create | `work-packages` |
| `custom_actions` | 3 | list, get, execute | `work-packages` |
| `queries` | 8 | list, get, get_default, create, update, delete, star, unstar | `queries` |
| `users` | 11 | list, get, create[admin], update[admin], list_roles, get_role, list_principals, list_project_members, list_user_projects, get_my_preferences, update_my_preferences | `users` |
| `placeholder_users` | 5 | list, get, create, update, delete[admin] | `users` |
| `memberships` | 5 | list, get, create, update, delete | `users` |
| `groups` | 2 | list, get | `users` |
| `time_entries` | 5 | list, create, update, delete, list_activities | `time` |
| `notifications` | 3 | list, mark_read, mark_all_read | `notifications` |
| `attachments` | 4 | upload, list, get, delete | `content` |
| `news` | 5 | list, get, create, update, delete | `content` |
| `documents` | 3 | list, get, update | `content` |
| `wiki` | 1 | get (integer ID only — API stub) | `content` |
| `storages` | 7 | list_storages, get_storage, list_project_storages, list/get/create/delete file_links | `storage` |
| `categories` | 2 | list, get | `projects` |
| `views` | 2 | list, get | `queries` |
| `costs` | 2 | list_budgets, get_budget | `finance` |
| `weekly_reports` | 4 | generate, this_week, last_week, raw_data | `reports` |
| `connection` | 2 | test_connection, check_permissions | `system` |

> **Note on `[admin]` tools:** tools marked `[admin]` require OpenProject administrator role. Non-admin deployments can hide them with `OPENPROJECT_MCP_EXCLUDE_TAGS=admin`.

---

## Quick start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- An OpenProject instance (cloud or self-hosted)
- An OpenProject API token — User menu → Account settings → Access tokens → + API Token

### Install and run

```bash
git clone https://github.com/gerket/openproject-mcp-server.git
cd openproject-mcp-server
uv sync

# Run the server (stdio transport for Claude Code)
OPENPROJECT_URL=https://your-instance.openproject.com \
OPENPROJECT_API_KEY=your-api-token \
uv run openproject-mcp
```

### Claude Code setup

Add to your project `.mcp.json` or global `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/openproject-mcp-server", "openproject-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-token",
        "OPENPROJECT_MCP_EXCLUDE_TAGS": "write"
      }
    }
  }
}
```

**Tip:** Start with `OPENPROJECT_MCP_EXCLUDE_TAGS=write` (read-only) for daily use. Expand to specific resources (e.g., `work-packages,projects`) or remove the filter for full access.

---

## Configuration

| Environment variable | Required | Description |
|---|---|---|
| `OPENPROJECT_URL` | ✅ | Base URL of your OpenProject instance |
| `OPENPROJECT_API_KEY` | ✅ | API token from Account settings → Access tokens |
| `OPENPROJECT_PROXY` | — | HTTP proxy URL (e.g. `http://proxy.company.com:8080`) |
| `OPENPROJECT_CA_BUNDLE` | — | Path to custom CA bundle for self-signed TLS certs |
| `OPENPROJECT_MCP_INCLUDE_TAGS` | — | Comma-separated tags — only expose matching tools |
| `OPENPROJECT_MCP_EXCLUDE_TAGS` | — | Comma-separated tags — hide matching tools |
| `LOG_LEVEL` | — | `DEBUG`, `INFO` (default), `WARNING`, `ERROR` |

---

## Tool filtering with tags

> **Migration (breaking):** the `core` / `situational` profile tags and their
> `*-read` / `*-write` derivatives have been removed in favor of per-endpoint
> resource tags. If you previously used `OPENPROJECT_MCP_INCLUDE_TAGS=core-read`,
> switch to an explicit recipe such as `OPENPROJECT_MCP_EXCLUDE_TAGS=write`
> (read-only) or list the resources you need (e.g., `work-packages,projects`).

Every tool carries up to 5 tags. Setting `OPENPROJECT_MCP_INCLUDE_TAGS` / `OPENPROJECT_MCP_EXCLUDE_TAGS` controls which tools are registered with the MCP client, improving Claude's tool selection accuracy by reducing noise.

### Tag types

| Tag | Values | Purpose |
|---|---|---|
| Access | `read`, `write` | Whether the tool reads or mutates data |
| Resource | 34 endpoint tags: `work-packages`, `activities`, `relations`, `hierarchy`, `watchers`, `types`, `statuses`, `priorities`, `projects`, `categories`, `versions`, `queries`, `views`, `users`, `groups`, `roles`, `memberships`, `placeholder-users`, `principals`, `preferences`, `time-entries`, `time-entry-activities`, `budgets`, `attachments`, `documents`, `news`, `wiki`, `storages`, `file-links`, `notifications`, `reminders`, `custom-actions`, `reports`, `system` | The API endpoint the tool targets — one per tool |
| Composite | `<resource>-read`, `<resource>-write` (e.g., `versions-read`, `time-entries-write`) | Select a resource AND an access level in one include filter |
| Permission | `admin` | Tools requiring OpenProject admin role |
| Name | `list_work_packages`, `create_query`, etc. | Exact function name — cherry-pick individual tools |

### Filtering examples

```bash
# Read-only server (all resources, reads only)
OPENPROJECT_MCP_EXCLUDE_TAGS=write

# Only work-package tools
OPENPROJECT_MCP_INCLUDE_TAGS=work-packages

# Work packages + projects, reads only
OPENPROJECT_MCP_INCLUDE_TAGS=work-packages,projects
OPENPROJECT_MCP_EXCLUDE_TAGS=write

# Everything except admin operations
OPENPROJECT_MCP_EXCLUDE_TAGS=admin

# Mixed: read versions but write time entries (composites)
OPENPROJECT_MCP_INCLUDE_TAGS=versions-read,time-entries-write

# Hide storage tools (no file server configured)
OPENPROJECT_MCP_EXCLUDE_TAGS=storages,file-links

# Full access — default when no env var is set
```

### Discovery tools

Two `system` tools help you inspect what's available:
- **`list_capabilities`** — returns a filter-aware summary of active tools (grouped by category, one-line descriptions) and inactive tools (when tag filters are applied). Includes the tag reference and configuration examples.
- **`describe_tool(tool_names: list[str])`** — returns full documentation for one or more tools by name, including inactive/filtered-out tools. The only way to inspect a tool that's been disabled.

---

## Running tests

```bash
# Unit tests (network-free, 192 tests)
uv sync --dev
uv run pytest

# Live integration tests against a real instance
# Run the one-time setup script first:
OPENPROJECT_URL=https://your-instance OPENPROJECT_API_KEY=your-token \
uv run python scripts/setup_test_project.py

# Then run the suite:
uv run pytest tests/integration -m integration -v

# Single module:
uv run pytest tests/integration/test_versions.py -m integration -v
```

See `docs/integration-test-setup.md` for the full click-ops checklist required to enable all 79 integration test scenarios.

---

## Notes on specific modules

**Custom actions:** `GET /custom_actions` (collection) returns 404 on Community Edition. Use `get_custom_action(id)` with a known ID discovered from the admin UI. `execute_custom_action` works on all editions.

**Costs / budgets:** The v3 API exposes budgets read-only (`list_budgets`, `get_budget`). Cost entry management (`/cost_types`, `/cost_entries`) is not in the core v3 spec — those endpoints return 404 on standard installations.

**Storage / file links:** Requires a file storage (OneDrive, Nextcloud) configured in Administration → File storages. Tools skip gracefully with informative messages when no storage is configured. Use `OPENPROJECT_MCP_EXCLUDE_TAGS=storage` to hide these tools on instances without file servers.

**Admin tools:** `create_user`, `update_user`, `delete_placeholder_user`, `create_project`, `delete_project` require administrator role. `delete_user` is not implemented — `DELETE /users/{id}` returns 403 via API regardless of role; use `update_user(status="locked")` to disable an account.

**Time entry activities:** The `/time_entries/activities` endpoint does not exist in v3. Activities are discovered via the create-form schema — the client fetches them automatically when needed.

**Custom fields:** Long-text/Markdown fields (`Formattable` type) are auto-wrapped to `{"raw": "..."}` by the client. A verify check raises loudly if a write is silently dropped.

**Attachments:** Uses OpenProject's two-part multipart upload (`metadata` JSON + `file` binary). Returns 500 on instances with misconfigured attachment storage.

---

## Architecture

```
src/
  client.py          — Async OpenProject API v3 client (aiohttp, retry/backoff)
  server.py          — FastMCP server + env-var tag filtering
  tools/             — One module per API domain (25 modules)
  utils/
    formatting.py    — Markdown formatters
    report_formatter.py — Weekly report generation
scripts/
  setup_test_project.py — One-time integration test environment setup
tests/
  unit/              — 192 network-free unit tests
  integration/       — 79 live integration tests (pytest -m integration)
docs/
  integration-test-setup.md — Click-ops checklist for test environment
  superpowers/plans/ — Phase-by-phase API coverage master plan
```

All tools return formatted Markdown strings and catch all exceptions via `format_error(...)`. The server dynamically computes the tool count at startup and logs it.

---

## API coverage

| Resource | Status | Notes |
|---|---|---|
| Work packages (full CRUD + filters) | ✅ | 18 tools |
| Projects, versions | ✅ | |
| Hierarchy, relations | ✅ | |
| Watchers, reminders, custom actions | ✅ | |
| Queries / saved views | ✅ | |
| Users, principals, placeholder users | ✅ | |
| Memberships, groups, roles | ✅ | |
| Time entries | ✅ | Activities via form schema |
| Notifications | ✅ | |
| Attachments | ✅ | |
| News, documents, wiki | ✅ | Documents: no create (API stub) |
| File storages, file links | ✅ | Requires configured storage |
| Categories, views | ✅ | Read-only |
| Budgets | ✅ (read-only) | No CRUD — v3 API is read-only for budgets |
| Cost entries | ❌ | Not in core v3 spec |
| Meetings, recurring meetings | ❌ | Planned — Phase I+ |
| Portfolios, programs | ❌ | EE-only paths |

---

## Contributing

```bash
uv sync --dev
uv run pre-commit install  # hooks: ruff, mypy, trailing whitespace, YAML/TOML
uv run pytest              # unit tests must pass before opening a PR
```

**Tag rule for new tools:** every `@mcp.tool` must carry `{access, category, tool_name}` at minimum, plus `{profile, composite}` if applicable. `test_full_sweep` in `tests/unit/test_tags.py` enforces that every tool has exactly one access tag and at least one non-access tag.

**Category tag table:**

| Tag | Modules |
|---|---|
| `work-packages` | work_packages, hierarchy, relations, watchers, reminders, custom_actions |
| `projects` | projects, versions, categories |
| `users` | users, placeholder_users, memberships, groups |
| `time` | time_entries |
| `content` | news, wiki, attachments, documents |
| `storage` | storages (file servers + file links) |
| `notifications` | notifications |
| `finance` | costs (budgets) |
| `reports` | weekly_reports |
| `system` | connection |
| `queries` | queries, views |
| `admin` | tools requiring administrator role |
