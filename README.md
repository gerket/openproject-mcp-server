# OpenProject MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server providing comprehensive integration with the [OpenProject](https://www.openproject.org/) API v3. Enables Claude and other MCP-compatible LLMs to read and manage projects, work packages, queries, attachments, notifications, time entries, and more.

![status](https://img.shields.io/badge/status-stable-brightgreen) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Tests](https://img.shields.io/badge/tests-153%20passing-brightgreen)

---

## Tools summary

94 tools across 18 modules, tagged for granular access control.

| Module | Tools | Category tag |
|---|---|---|
| `work_packages` | list, search, create, update, delete, assign, comment, activities, types, statuses, priorities, overdue, due_soon, unassigned, recently_created, high_priority, nearly_complete | `work-packages` |
| `projects` | list, get, create, update, delete, subprojects | `projects` |
| `versions` | list, create | `projects` |
| `hierarchy` | set_parent, remove_parent, list_children | `work-packages` |
| `relations` | create, list, get, update, delete | `work-packages` |
| `watchers` | list_watchers, list_available_watchers, add_watcher, remove_watcher, get_activity, update_activity, list_available_assignees | `work-packages` |
| `reminders` | list, create | `work-packages` |
| `queries` | list, get, get_default, create, update, delete, star, unstar | `queries` |
| `users` | list, get, roles, project_members, user_projects | `users` |
| `memberships` | list, get, create, update, delete | `users` |
| `groups` | list, get | `users` |
| `time_entries` | list, create, update, delete, activities | `time` |
| `notifications` | list, mark_read, mark_all_read | `notifications` |
| `attachments` | upload, list, get, delete | `content` |
| `news` | list, get, create, update, delete | `content` |
| `wiki` | get (by integer ID — API stub) | `content` |
| `costs` | list_types, list_entries, create, update, delete | `finance` |
| `weekly_reports` | generate, this_week, last_week, raw_data | `reports` |
| `connection` | test_connection, check_permissions | `system` |

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
uv run python openproject-mcp-fastmcp.py

# Or using the installed CLI entrypoint
OPENPROJECT_URL=... OPENPROJECT_API_KEY=... uv run openproject-mcp
```

### Claude Code setup

Add to your project `.mcp.json` or global `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/openproject-mcp-server", "python", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-token",
        "OPENPROJECT_MCP_INCLUDE_TAGS": "core-read"
      }
    }
  }
}
```

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

Every tool carries up to 5 tags. Setting `OPENPROJECT_MCP_INCLUDE_TAGS` / `OPENPROJECT_MCP_EXCLUDE_TAGS` controls which tools are registered with the MCP client, improving Claude's tool selection accuracy by reducing noise.

### Tag types

| Tag | Values | Purpose |
|---|---|---|
| Access | `read`, `write` | Whether the tool reads or mutates data |
| Category | `work-packages`, `projects`, `queries`, `users`, `time`, `content`, `notifications`, `finance`, `reports`, `system` | API domain |
| Profile | `core`, `situational` | Frequency of use |
| Composite | `core-read`, `core-write`, `situational-read`, `situational-write` | AND-style filter (access × profile) |
| Catch-all | `all` | Every tool — opt-in to full set explicitly |

### Profile definitions

**`core`** (~20 tools) — every session:
`list_work_packages`, `search_work_packages`, `create_work_package`, `update_work_package`, `add_work_package_comment`, `list_work_package_activities`, `list_projects`, `get_project`, `list_types`, `list_statuses`, `list_priorities`, `list_users`, `get_user`, `list_notifications`, `mark_all_notifications_read`, `list_queries`, `get_query`, `create_query`, `list_versions`, `test_connection`

**`situational`** (~34 tools) — specific tasks:
relations, hierarchy, watchers, reminders, time entries, attachments, news, wiki, weekly_reports, `list_available_assignees`, `get_activity`, `update_activity`

**No profile** — admin/niche/module-gated tools (memberships, costs, overdue/filter conveniences, etc.)

### Filtering examples

```bash
# Core reads only — recommended default (~15 tools)
OPENPROJECT_MCP_INCLUDE_TAGS=core-read

# All core tools (read + write, ~20 tools)
OPENPROJECT_MCP_INCLUDE_TAGS=core

# Core + situational reads (research/reporting)
OPENPROJECT_MCP_INCLUDE_TAGS=core-read,situational-read

# Everything except finance
OPENPROJECT_MCP_EXCLUDE_TAGS=finance

# Full access — default when no env var is set
```

---

## Running tests

```bash
# Unit tests (network-free, 153 tests)
uv sync --extra dev
uv run pytest

# Live integration tests against a real instance
OPENPROJECT_URL=https://your-instance OPENPROJECT_API_KEY=your-token \
uv run python test_live_integration.py
```

The live integration test covers 13 API domains with full CRUD lifecycles. See `docs/integration-test-setup.md` for admin configuration steps needed to enable all test scenarios.

---

## Notes on specific modules

**Wiki:** The OpenProject v3 API wiki support is a stub — only `GET /wiki_pages/{id}` (by integer ID) exists. `get_wiki_page(wiki_page_id)` is the only wiki tool.

**Costs:** Requires the Costs module in Administration → Modules. Returns 404 otherwise.

**Custom fields:** Long-text/Markdown fields (`Formattable` type) are auto-wrapped to `{"raw": "..."}` by the client. A verify check raises loudly if a write is silently dropped.

**Attachments:** Uses OpenProject's two-part multipart upload (`metadata` JSON + `file` binary).

---

## Architecture

```
src/
  client.py          — Async OpenProject API v3 client (aiohttp, retry/backoff)
  server.py          — FastMCP server + env-var tag filtering
  tools/             — One module per API domain
  utils/
    formatting.py    — Markdown formatters
    report_formatter.py — Weekly report generation
```

All tools return formatted Markdown strings and catch all exceptions via `format_error(...)`. The server dynamically computes the tool count at startup.

---

## Contributing

```bash
uv sync --extra dev
uv run pre-commit install  # hooks: ruff, mypy, trailing whitespace, YAML/TOML
uv run pytest              # must pass before opening a PR
```

Tag rule for new tools: every `@mcp.tool` must carry `{access, category, profile_if_applicable, composite_if_applicable, "all"}`. `test_full_sweep` in `test_tags.py` enforces this in CI.
