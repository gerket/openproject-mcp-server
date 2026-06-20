# Changelog

## [3.1.0](https://github.com/gerket/openproject-mcp-server/compare/v3.0.0...v3.1.0) (2026-06-20)


### Features

* **ci:** require scope in all PR titles, force 4.0.0 release ([#31](https://github.com/gerket/openproject-mcp-server/issues/31)) ([b19be6a](https://github.com/gerket/openproject-mcp-server/commit/b19be6a27883cc9a5810e27bbcce16965326f577))


### Bug Fixes

* **ci:** upgrade release-please-action to v5 (node24), drop invalid package-name input ([#28](https://github.com/gerket/openproject-mcp-server/issues/28)) ([af48754](https://github.com/gerket/openproject-mcp-server/commit/af48754aa33134eed0c84e56391d22e161b552bc))
* **release:** add packages section with include-component-in-tag false ([#34](https://github.com/gerket/openproject-mcp-server/issues/34)) ([49620b5](https://github.com/gerket/openproject-mcp-server/commit/49620b55e90d2e15e23a3e7c9f90379f302fecaa))
* **release:** set manifest version to 3.0.0 to match last tag ([#33](https://github.com/gerket/openproject-mcp-server/issues/33)) ([bfd04a1](https://github.com/gerket/openproject-mcp-server/commit/bfd04a1a98f07509bf5a0bba71722451c9df0a75))


### Documentation

* **docs:** never enable auto-merge when opening a PR ([#35](https://github.com/gerket/openproject-mcp-server/issues/35)) ([c7ab0cd](https://github.com/gerket/openproject-mcp-server/commit/c7ab0cd896a7aaa85240e803d6735aa7ba5a19a8))

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
