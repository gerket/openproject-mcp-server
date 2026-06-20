# OpenProject MCP — Full API Coverage Master Plan

> This is a **multi-session coordination document**, not an implementation plan.
> Each phase below will produce its own task-level implementation plan
> (via `superpowers:writing-plans`) before execution begins.
>
> **Status tracking:** Update the ✅/🔲 column as phases complete.

---

## Goal

Ship a production-ready, fully-tested MCP server with complete coverage of the
actionable OpenProject v3 API, read/write access control via tags, CI, and
documentation thorough enough for a stranger to deploy and test it.

---

## Current state (as of 2026-06-19)

- **PR #2 merged** (Phase 0 + Phase A): 94 tools, all tagged, CI green, pytest 153 tests, pre-commit enforced.
- **PR #3 merged** (Phase B): watchers, activity edit, available assignees, reminders — 86 tools on main.
- **PR #4 merged** (Phase C): queries (8 tools) + profile tags + env-var filtering — 94 tools on main.
- **PR #5 open** (Phase D): custom actions (3 tools) + version update/delete (2 tools) + tests/ reorganisation — 99 tools, 162 tests when merged.
- **Main branch** is at the Phase C merge (94 tools, 153 tests).
- **Next phase after PR #5 merges:** Phase E (Users, principals, user preferences — ~10 tools).

---

## Tag Convention

Every tool carries **up to 5 tags**: access + category + profile + composite + `"all"`.

```python
# Core read tool — 5 tags
@mcp.tool(tags={"read", "work-packages", "core", "core-read", "list_work_packages"})
async def list_work_packages(...) -> str: ...

# Situational write tool — 5 tags
@mcp.tool(tags={"write", "work-packages", "situational", "situational-write", "create_time_entry"})
async def create_time_entry(...) -> str: ...

# No-profile tool (admin/niche) — 3 tags
@mcp.tool(tags={"read", "users", "list_memberships"})
async def list_memberships(...) -> str: ...
```

### Access tags
- `"read"` — GET operations, no side effects
- `"write"` — POST/PATCH/DELETE operations

### Category tags

| Tag | Tool modules |
|---|---|
| `work-packages` | work_packages, hierarchy, relations, watchers, reminders |
| `projects` | projects, versions |
| `users` | users, memberships, groups, placeholder_users |
| `time` | time_entries |
| `content` | news, wiki, attachments, documents |
| `storage` | storages, project_storages, file_links (external file-server integration) |
| `notifications` | notifications |
| `finance` | costs |
| `reports` | weekly_reports |
| `system` | connection |
| `queries` | queries |

### Permission tags

- `"admin"` — tools that require OpenProject administrator role to succeed. Callers using a non-admin API token can exclude these with `OPENPROJECT_MCP_EXCLUDE_TAGS=admin` to avoid confusing 403 errors. Applies to: `create_user`, `update_user`, `delete_placeholder_user`, `create_project`, `delete_project`. **Note:** `delete_user` is not implemented — `DELETE /users/{id}` returns 403 even for system admins via API; use `update_user(status="locked")` to disable an account instead.

### Profile tags

- `"core"` — ~20 tools for every session (common WP operations, list/get projects, users, notifications, queries, versions)
- `"situational"` — ~34 tools for specific tasks (relations, hierarchy, watchers, time entries, attachments, news, etc.)
- `"all"` — every tool (no-profile tools only get this)

### Composite tags (AND-style filtering within FastMCP's OR semantics)

- `"core-read"`, `"core-write"`, `"situational-read"`, `"situational-write"`

### Env-var filtering

Set `OPENPROJECT_MCP_INCLUDE_TAGS` and/or `OPENPROJECT_MCP_EXCLUDE_TAGS` (comma-separated) to control which tools are exposed:

| Goal | Env var |
|---|---|
| Core reads only (~15 tools, optimal daily use) | `OPENPROJECT_MCP_INCLUDE_TAGS=core-read` |
| All core (read + write, ~20 tools) | `OPENPROJECT_MCP_INCLUDE_TAGS=core` |
| Core + situational reads | `OPENPROJECT_MCP_INCLUDE_TAGS=core-read,situational-read` |
| Everything except finance | `OPENPROJECT_MCP_EXCLUDE_TAGS=finance` |
| Non-admin token (hide admin-only tools) | `OPENPROJECT_MCP_EXCLUDE_TAGS=admin` |
| No file storage configured | `OPENPROJECT_MCP_EXCLUDE_TAGS=storage` |
| Show only admin tools | `OPENPROJECT_MCP_INCLUDE_TAGS=admin` |
| Full access (default) | *(no env var)* |

All new tools must carry all applicable tags. The `test_full_sweep`
test in `test_tags.py` enforces that every tool has at least one tag; extend it
to enforce the two-tag contract as well.

---

## Phase Sequence

```
Phase 0  ✅ COMPLETE  — Read/write + category tags on all tools (PR #2)
Phase A  ✅ COMPLETE  — CI + pytest + pre-commit + pyproject.toml (PR #2)
Phase B  ✅ COMPLETE  — WP sub-resources: watchers, activity edit, assignees, reminders (PR #3)
Phase C  ✅ COMPLETE  — Queries (saved views) + profile tags + env-var filtering (PR #4)
Phase D  ✅ COMPLETE  — Custom actions + version lifecycle + tests/ reorganisation (PR #5)
Phase E  ✅ COMPLETE  — Users, principals, placeholder users, preferences + admin tag (PR #6)
Phase F  ✅ COMPLETE  — Documents, storages, file links + budget read tools (PR #7)
Phase G  ✅ COMPLETE  — Categories, views (PR #7, shipped with Phase F)
Phase H  🔲 IN PROGRESS — README rewrite + master plan update
```

---

## Phase 0 — Tag all existing tools ✅ COMPLETE

PR #2 delivers: 94 tools, access + category tags, 0 untagged. PR #3 adds profile
tags (core/situational/all) and composite tags (core-read, etc.) to all tools.
Env-var filtering (`OPENPROJECT_MCP_INCLUDE_TAGS` / `OPENPROJECT_MCP_EXCLUDE_TAGS`)
landed in PR #4.

---

## Phase A — CI + pytest migration + pyproject.toml cleanup ✅ COMPLETE

PR #2 delivers: `uv run pytest` runs all 153 tests, GitHub Actions CI on
Python 3.10/3.11/3.12, pre-commit (ruff + mypy), version 2.0.0, `openproject-mcp`
CLI entrypoint.

---

## Phase B — WP sub-resources ✅ COMPLETE

PR #3 delivers: 9 new tools (watchers ×4, activity get/edit, available assignees,
reminders ×2). Tool count 86 on main.

---

## Phase C — Queries (saved views) 🔲 IN PR #4

**Goal:** A stranger can clone the repo, run one command, and see all tests
pass. Every PR is gated by CI.

### A-1: Migrate tests to pytest

**Current state:** 15 test files use `asyncio.run()` + `if __name__ == "__main__"`.
No test runner can discover them. Converting to pytest + pytest-asyncio makes
`uv run pytest` the single entry point.

**What to change:**
- Add `pytest>=7.0`, `pytest-asyncio>=0.23` to `[project.optional-dependencies].dev`
- Add `[tool.pytest.ini_options]` to `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["."]
  python_files = "test_*.py"
  python_functions = "test_*"
  ```
- Convert all `async def test_*()` functions — they already have the right
  names; `asyncio_mode = "auto"` means no other change is needed per test
- Remove `if __name__ == "__main__":` blocks (pytest doesn't need them;
  the files can still be run directly for development)
- The live integration test (`test_live_integration.py`) should be excluded
  from the default pytest run (it requires real credentials):
  add `--ignore=test_live_integration.py` to `addopts` in pytest config, and
  document running it separately

**Files:** all 14 unit test files + `pyproject.toml`

### A-2: Fix pyproject.toml

- `authors`: replace placeholder with real name/email
- `version`: bump to `2.0.0` (77 tools, tags, bug fixes, new modules)
- `[tool.black] target-version`: change `['py38']` → `['py310', 'py311', 'py312']`
- Add `[project.scripts]` entrypoint:
  ```toml
  [project.scripts]
  openproject-mcp = "src.server:main"
  ```
  (requires adding a `main()` function to `src/server.py` that calls `mcp.run(transport="stdio")`)
- Add mypy to dev deps: `mypy>=1.0`, `pytest-mypy>=0.10`

### A-3: GitHub Actions CI

Create `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --extra dev
      - run: uv run pytest --tb=short
```

**Deliverable:** `uv run pytest` → green, CI runs on every PR.

---

## Phase B — WP sub-resources 🔲

**New tools (~9):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_watchers` | read | `GET /work_packages/{id}/watchers` |
| `list_available_watchers` | read | `GET /work_packages/{id}/available_watchers` |
| `add_watcher` | write | `POST /work_packages/{id}/watchers` |
| `remove_watcher` | write | `DELETE /work_packages/{id}/watchers/{user_id}` |
| `get_activity` | read | `GET /activities/{id}` |
| `update_activity` | write | `PATCH /activities/{id}` — edit comment; body: `{"comment": {"raw": "..."}, "internal": false}` |
| `list_available_assignees` | read | `GET /work_packages/{id}/available_assignees` |
| `list_reminders` | read | `GET /work_packages/{id}/reminders` |
| `create_reminder` | write | `POST /work_packages/{id}/reminders` |

**Notes:**
- `update_activity`: requires "edit journals" permission; `lockVersion` not needed
- `list_available_assignees` is better than `list_users` for the "who can I assign to" case
- Reminders: check if GET returns IDs; if yes, add `delete_reminder(reminder_id)` too
- All tools follow `src/tools/` module pattern; add `tags={"read"/"write"}`
- Integration test: add watcher, verify in list, remove watcher

**Live integration test additions:**
```
watchers/add_watcher(wp_id=46, user_id=5)   → verify list_watchers count=1
watchers/remove_watcher(wp_id=46, user_id=5) → verify list_watchers count=0
activities/get_activity(activity_id)          → from list_work_package_activities
activities/update_activity                    → edit a comment, verify updated
available_assignees/list(wp_id=46)            → non-empty list
```

---

## Phase C — Queries (saved views) 🔲

**New tools (~8):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_queries` | read | `GET /queries` — accepts optional `project_id` filter |
| `get_query` | read | `GET /queries/{id}` |
| `get_default_query` | read | `GET /queries/default` |
| `create_query` | write | `POST /queries` |
| `update_query` | write | `PATCH /queries/{id}` |
| `delete_query` | write | `DELETE /queries/{id}` |
| `star_query` | write | `PATCH /queries/{id}/star` |
| `unstar_query` | write | `PATCH /queries/{id}/unstar` |

**This is the most complex phase.** Query payloads have nested HAL structure:

```json
{
  "name": "My open bugs",
  "public": false,
  "_links": {
    "project": {"href": "/api/v3/projects/4"},
    "columns": [
      {"href": "/api/v3/queries/columns/id"},
      {"href": "/api/v3/queries/columns/subject"},
      {"href": "/api/v3/queries/columns/status"}
    ],
    "sortBy": [
      {"href": "/api/v3/queries/sort_bys/id-desc"}
    ]
  },
  "filters": [
    {
      "_type": "StatusQueryFilter",
      "_links": {
        "filter": {"href": "/api/v3/queries/filters/status"},
        "operator": {"href": "/api/v3/queries/operators/o"}
      }
    }
  ]
}
```

**Notes:**
- `create_query` input model: `name`, `public`, optional `project_id`, optional
  `filters` (array of filter dicts), optional `column_names` (list of column
  name strings that the tool converts to hrefs)
- Expose a simplified API that hides the HAL link construction — callers pass
  `column_names=["id", "subject", "status"]` and the tool converts to hrefs
- `list_queries` should filter by project_id to avoid listing all global queries
- Unit tests mock the full HAL response; integration test creates a query,
  stars it, updates name, unstar, delete

**Live integration test additions:**
```
queries/create(name="integration-test-query", project_id=4)  → id
queries/get(id)
queries/star(id)
queries/update(id, name="integration-test-query-updated")
queries/unstar(id)
queries/delete(id)
```

---

## Phase D — Custom actions + version lifecycle 🔲

**New tools (~5):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_custom_actions` | read | `GET /custom_actions` |
| `get_custom_action` | read | `GET /custom_actions/{id}` |
| `execute_custom_action` | write | `POST /custom_actions/{id}/execute` — body: `{"_links": {"workPackage": {"href": "/api/v3/work_packages/{id}"}}, "lockVersion": N}` |
| `update_version` | write | `PATCH /versions/{id}` — same lockVersion pattern as WPs |
| `delete_version` | write | `DELETE /versions/{id}` |

**Notes:**
- `execute_custom_action` requires GET for lockVersion first
- Custom actions are workflow buttons defined by admins; listing them first
  lets the agent discover names before executing
- `update_version` + `delete_version` complete the version lifecycle (create
  already exists)
- `delete_version` may fail if WPs are assigned — tool should surface the
  error message clearly

**Admin setup needed for integration test:**
- Create at least one custom action in OpenProject admin (Administration →
  Work packages → Custom actions) targeting the infrastructure project,
  Task type, New→In Progress transition. Note the action ID.

**Live integration test additions:**
```
custom_actions/list → at least 1 action
custom_actions/get(id)
custom_actions/execute(action_id, wp_id=46) → verify WP status changed
versions/create → update name → delete
```

---

## Phase E — Users, principals, user preferences 🔲

**New tools (~10):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_principals` | read | `GET /principals` — optional `project_id` filter |
| `update_user` | write | `PATCH /users/{id}` — admin only |
| `delete_user` | write | `DELETE /users/{id}` — admin only |
| `list_placeholder_users` | read | `GET /placeholder_users` |
| `get_placeholder_user` | read | `GET /placeholder_users/{id}` |
| `create_placeholder_user` | write | `POST /placeholder_users` |
| `update_placeholder_user` | write | `PATCH /placeholder_users/{id}` |
| `delete_placeholder_user` | write | `DELETE /placeholder_users/{id}` |
| `get_my_preferences` | read | `GET /my_preferences` |
| `update_my_preferences` | write | `PATCH /my_preferences` |

**Notes:**
- `list_principals` returns users + groups + placeholder users in one call;
  more useful than separate `list_users` + `list_groups` for assignment UX
- `update_user`/`delete_user`: document "requires admin" in tool description;
  graceful 403 handling
- `update_my_preferences`: payload includes `timeZone`, `wantsNewsletters`,
  `dailyReminders`, `pauseReminders` — expose as simple kwargs
- Integration test uses create/update/delete on placeholder users (safe —
  no real account affected)

**Live integration test additions:**
```
principals/list → non-empty
my_preferences/get → verify timezone field present
placeholder_users/create → get → update → delete lifecycle
```

---

## Phase F — Budgets, documents, file links, storages 🔲

**New tools (~11):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_budgets` | read | `GET /budgets` |
| `get_budget` | read | `GET /budgets/{id}` |
| `list_documents` | read | `GET /documents` |
| `get_document` | read | `GET /documents/{id}` |
| `update_document` | write | `PATCH /documents/{id}` |
| `list_storages` | read | `GET /storages` |
| `get_storage` | read | `GET /storages/{id}` |
| `list_file_links` | read | `GET /work_packages/{id}/file_links` |
| `get_file_link` | read | `GET /file_links/{id}` |
| `create_file_links` | write | `POST /work_packages/{id}/file_links` |
| `delete_file_link` | write | `DELETE /file_links/{id}` |

**Notes:**
- Budgets: read-only in Community edition; write (create/update) requires
  Costs module — implement all CRUD but document gating
- Documents: no POST (legacy form only) — list/get/update only
- File links require a configured storage (OneDrive/Nextcloud) — tools
  return informative errors when no storages exist
- `list_storages` must precede `create_file_links` in any agent workflow
- No `open_file_link` tool (returns 303 redirect; client-side only)

**Admin setup needed for integration test:**
- Budgets: Costs module must be enabled in Administration → Modules
- File links: an OneDrive or Nextcloud storage must be configured in
  Administration → File storages; then linked to project 4

**Live integration test additions:**
```
budgets/list    → SKIP if Costs module not enabled, else list
documents/list  → may be empty, assert no error
storages/list   → may be empty, assert no error
file_links/list(wp_id=46) → may be empty, assert no error
```

---

## Phase G — Categories, views 🔲

**New tools (~4):**

| Tool | Tag | Endpoint |
|---|---|---|
| `list_categories` | read | `GET /projects/{id}/categories` |
| `get_category` | read | `GET /categories/{id}` |
| `list_views` | read | `GET /views` |
| `get_view` | read | `GET /views/{id}` |

**Notes:**
- Categories are project-scoped labels (distinct from WP type); may be empty
  on instances that don't use them
- Views surface named configurations (table, gantt, calendar) that wrap
  queries; read-only from the API — creation/update is via Phase C queries
- All tools in this phase are read-only, no write counterparts

**Admin setup needed for integration test:**
- Create at least one Category in project 4 (Administration → Projects →
  infrastructure → Categories → New category "Test Category")

**Live integration test additions:**
```
categories/list(project_id=4) → ≥1 if admin created one, else SKIP
views/list → may be empty, assert no error
```

---

## Phase H — README rewrite + integration test setup guide 🔲

**Goal:** A developer with a fresh OpenProject instance can follow the README
and `docs/integration-test-setup.md` to get from zero to all 54+ integration
tests green, including the admin-gated tests.

### H-1: README rewrite

Replace the current stale README with:

1. **What this is** — 1 paragraph, link to OpenProject
2. **Tools summary** — table of all tool modules, count, brief description
3. **Quick start** — clone → `uv sync` → set env vars → `uv run pytest`
4. **Claude Code setup** — exact `.mcp.json` snippet; how to use
   `allowedTools` with `read`/`write` tags for granular permission control
5. **Configuration** — all env vars (`OPENPROJECT_URL`, `OPENPROJECT_API_KEY`,
   `OPENPROJECT_PROXY`, `LOG_LEVEL`)
6. **Running the server** — `uv run python openproject-mcp-fastmcp.py`
   (stdio) or `uv run openproject-mcp` (after Phase A installs the script)
7. **Running tests** — `uv run pytest` for unit tests;
   `OPENPROJECT_URL=... uv run python test_live_integration.py` for live tests
8. **Contributing** — tag convention, test requirements, commit format
9. **API coverage table** — which endpoints are covered vs excluded and why

### H-2: Integration test setup guide (`docs/integration-test-setup.md`)

Step-by-step admin click-ops document for configuring a fresh OpenProject
instance to support all integration tests, including the currently-skipped
admin-gated fields.

**Contents:**

#### Required: Base setup (needed for 54 currently-passing tests)
- Create a project named "infrastructure" (ID 4 is assigned by OpenProject
  automatically on a fresh install — or update `test_live_integration.py`
  to discover the project by name if ID differs)
- Create a work package of type Task in that project, subject "test" (this
  becomes WP #46 or whatever ID — the test should discover by subject search)
- Create an API token for the test user: User menu → Account settings →
  Access tokens → + API Token. Store as `openproject-api-token-tom` in
  Infisical (or set `OPENPROJECT_API_KEY` env var directly)

#### Required: Custom field setup (for all CF types to be tested)
For each field below, go to Administration → Custom fields → Work packages → Create:

| Field name | Field type | Applies to | Notes |
|---|---|---|---|
| `jira_key` | Text (String) | Task, Epic, Bug | CF2 |
| `trigger` | Long text (Formattable) | Task, Epic, Bug | CF3 |
| `test_boolean` | Boolean | Task | CF4 |
| `test_date` | Date | Task | CF5 |
| `test_float` | Float | Task | CF6 |
| `test_integer` | Integer | Task | CF8 |
| `test_link` | URL (Link) | Task | CF9 |
| `test_text` | Text (String) | Task | CF11 |
| `test_long_text` | Long text (Formattable) | Task | CF15 |
| `test_list` | List | Task | CF10 — add options: "Option A", "Option B" |
| `test_user` | User | Task | CF12 — after creating, add test user to project |
| `test_version` | Version | Task | CF13 — requires a version in the project |
| `test_heirarchy` | Hierarchy | Task | CF7 — add root item "Item A" |
| `test_weighted_item_list` | Hierarchy | Task | CF14 — add root item "Item B" |

After creating each CF, go to the infrastructure project → Settings →
Custom fields and enable each one.

#### Required: Add test user to infrastructure project
Administration → Projects → infrastructure → Members → + Member → add test
user with "Member" role. This enables CF12 ([]User) testing.

#### Required for Phase D: Custom action setup
Administration → Work packages → Custom actions → + Custom action:
- Name: "Start work"
- Conditions: Status = New
- Actions: Status → In Progress
- Available for: Task type in infrastructure project

#### Required for Phase F: Costs module (for budgets)
Administration → Modules → enable "Time and costs" and "Budgets"

#### Required for Phase F: File storage (for file links)
Administration → File storages → + Storage → configure OneDrive or Nextcloud.
Then project → Settings → File storages → link the storage.

#### Running the full live test suite after setup:
```bash
OPENPROJECT_URL=https://your-instance.openproject.com \
OPENPROJECT_API_KEY=your-api-token \
uv run python test_live_integration.py
```

Expected: all tests pass including previously-skipped CF10/CF12/CF13/CF14.

---

## What is explicitly excluded

| Resource | Reason |
|---|---|
| Wiki write (list/create/update/delete) | API stub — v3 endpoints don't exist yet |
| OAuth 2 management | Credential management, never in an MCP |
| Grids | Dashboard widget layout, no AI project-management value |
| Sprints | Undocumented Enterprise feature |
| Programs / Portfolios | No POST (create), Enterprise-tier |
| Work Schedule (days) | Read-only calendar metadata |
| User Working Times | HR/capacity planning, niche |
| Project Phase Definitions/Phases | Read-only stubs |
| Previewing | HTML render endpoint, UI-only |
| Revisions | Source control links, read-only |
| Workspaces | Enterprise tier, minimal public docs |
| `open_file_link` | Returns 303 redirect — client-side only |

---

## Session handoff protocol

Before starting any phase:
1. Check this file — confirm the phase is still 🔲 (not already complete)
2. `git log --oneline -10` in the repo to see what's landed
3. Confirm the current PR is merged before starting work that builds on it
4. Create a task-level plan using `superpowers:writing-plans`
5. Execute using `superpowers:subagent-driven-development`
6. Update this file's status column when the PR merges

## Dependency order rationale

```
PR #2 merge
  └─ Phase A (CI/pytest/packaging)  ← prerequisite for everything else
       └─ Phase B (WP sub-resources)
       └─ Phase C (Queries)         ← needed before Phase G (views reference queries)
       └─ Phase D (Custom actions + version lifecycle)
       └─ Phase E (Users/principals)
       └─ Phase F (Budgets/docs/file links)
            └─ Phase G (Categories/views/storages)
                 └─ Phase H (README + setup guide)  ← last, documents final state
```

## Related files

- Feature branch plans: `docs/superpowers/plans/2026-06-17-wiki-groups-notifications-attachments-costs.md`
- Phase 0 plan: `docs/superpowers/plans/2026-06-19-phase-0-tag-all-tools.md`
- Handoff log: `docs/handoff.md`
