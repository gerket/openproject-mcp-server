# Changelog

## [3.1.0](https://github.com/gerket/openproject-mcp-server/compare/v3.0.0...v3.1.0) (2026-06-20)


### Features

* **ci:** require scope in all PR titles, force 4.0.0 release ([#31](https://github.com/gerket/openproject-mcp-server/issues/31)) ([2405955](https://github.com/gerket/openproject-mcp-server/commit/240595586b3c8c67773aa224be8b2cd2c4020295))


### Bug Fixes

* **ci:** upgrade release-please-action to v5 (node24), drop invalid package-name input ([#28](https://github.com/gerket/openproject-mcp-server/issues/28)) ([d696392](https://github.com/gerket/openproject-mcp-server/commit/d69639249b0c5ad3b174ca52a3239e3c39519b68))
* **release:** add packages section with include-component-in-tag false ([#34](https://github.com/gerket/openproject-mcp-server/issues/34)) ([931ca65](https://github.com/gerket/openproject-mcp-server/commit/931ca6558c5c525b90e29350bebefb10d668a8ed))
* **release:** set manifest version to 3.0.0 to match last tag ([#33](https://github.com/gerket/openproject-mcp-server/issues/33)) ([307d8c2](https://github.com/gerket/openproject-mcp-server/commit/307d8c260e88ae585b0797008ebebdcc2ce101b5))


### Documentation

* **docs:** document BREAKING CHANGE footer convention for major releases ([#42](https://github.com/gerket/openproject-mcp-server/issues/42)) ([54a4ee1](https://github.com/gerket/openproject-mcp-server/commit/54a4ee1088870db81ef67b2a2bb01d93190f0364))
* **docs:** never enable auto-merge when opening a PR ([#35](https://github.com/gerket/openproject-mcp-server/issues/35)) ([0a25eee](https://github.com/gerket/openproject-mcp-server/commit/0a25eee848f23f97d58f3a1e60a3c3911a096ede))

## [3.0.0] — 2026-06-20

Complete rewrite from a single-file monolith to a modular 25-module server.

### Added
- **120 tools** across 25 modules covering the full actionable OpenProject v3 API
- **Tag-based filtering** — `read`/`write`, category, `admin`, `core`/`situational`, composite tags; control exposed tools with `OPENPROJECT_MCP_INCLUDE_TAGS` / `OPENPROJECT_MCP_EXCLUDE_TAGS`
- **`admin` permission tag** — hide admin-only tools from non-admin tokens with `OPENPROJECT_MCP_EXCLUDE_TAGS=admin`
- **`storage` category tag** — hide file-server tools on instances without OneDrive/Nextcloud
- Phase E: user management (`create_user`, `update_user`), principals, placeholder users, preferences
- Phase F: documents (list/get/update), file storages, file links (list/get/create/delete), project-storage links
- Phase G: work package categories, views
- Phase D: custom actions (list/get/execute), version lifecycle (update/delete)
- Phase C: saved queries (full CRUD + star/unstar), env-var tag filtering
- Phase B: watchers, activity editing, available assignees, reminders
- **192 unit tests** + **79 live integration tests** with a one-time setup script (`scripts/setup_test_project.py`)
- Integration test bot user (`mcp-test-bot`) for notification testing
- `api_paths` session fixture — skips tests with spec-based messages for absent endpoints
- Release workflow (`.github/workflows/release.yml`)

### Changed
- Modular architecture: `src/tools/` (25 modules) replacing single-file implementation
- `uv` replaces pip; `uv run openproject-mcp` is the canonical run command
- Tests restructured: `tests/unit/` (192 tests) + `tests/integration/` (79 tests)
- `get_time_entry_activities` now uses form schema (no `/time_entries/activities` endpoint in v3)
- `get_memberships` filter fixed: `user` → `principal`
- `update_activity` payload fixed: `{"comment": "string"}` not `{"comment": {"raw": "..."}}`
- Server startup: import errors propagate immediately — no silent partial loading

### Removed
- Single-file `openproject-mcp.legacy.py` (135KB)
- Non-functional entry point scripts (`openproject-mcp-http.py`, `-sse.py`, `-fastmcp.py`)
- `requirements.txt` — `pyproject.toml` is the source of truth
- Cost entry tools (`list_cost_types`, `list_cost_entries`, create/update/delete) — endpoints not in core v3 API; replaced with `list_budgets` + `get_budget`

### Fixed
- `conftest.py` default project slug `"infrastructure"` → `"mcp-test"`
- Stale `--ignore=test_live_integration.py` in `pyproject.toml` addopts
- `check_permissions` now tagged `core`/`core-read`
- `assign_work_package`, `unassign_work_package` now tagged `situational`
- `mark_notification_read`, `generate_this_week_report`, `generate_last_week_report` now tagged `situational`

## [2.0.0] — 2026-06-19

Initial modular rewrite — CI, pytest, pre-commit, packaging, tag system introduced.

## [1.0.0] — 2026-06-16

Original single-file implementation (`openproject-mcp.legacy.py`).
