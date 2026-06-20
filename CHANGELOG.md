# Changelog

## [4.0.0](https://github.com/gerket/openproject-mcp-server/compare/v3.0.0...v4.0.0) (2026-06-20)


### Features

* **ci:** add lint job (ruff + mypy) and fix lint debt ([#19](https://github.com/gerket/openproject-mcp-server/issues/19)) ([9097c62](https://github.com/gerket/openproject-mcp-server/commit/9097c626754611cc11ead4d1a4c19dbcd1dac6bb))
* **ci:** require scope in all PR titles, force 4.0.0 release ([#31](https://github.com/gerket/openproject-mcp-server/issues/31)) ([b19be6a](https://github.com/gerket/openproject-mcp-server/commit/b19be6a27883cc9a5810e27bbcce16965326f577))
* **docs:** README rewrite for 120-tool state + mark E/F/G complete ([#8](https://github.com/gerket/openproject-mcp-server/issues/8)) ([dd823e3](https://github.com/gerket/openproject-mcp-server/commit/dd823e3a1bb3852371bb839bf9b4499ba8a6879b))
* **server:** new API domains, read/write tags, CI, pytest, pre-commit (Phase 0 + Phase A) ([#2](https://github.com/gerket/openproject-mcp-server/issues/2)) ([6e7312d](https://github.com/gerket/openproject-mcp-server/commit/6e7312d28955cd88ced5d42be8164d0e8d403283))
* **server:** self-hosting enhancements: custom-field values, retry/backoff, custom CA, workflow-aware transitions ([#1](https://github.com/gerket/openproject-mcp-server/issues/1)) ([0a3d8b0](https://github.com/gerket/openproject-mcp-server/commit/0a3d8b09937a9b6be625ac42f148bdb715856693))
* **tools:** custom actions + version lifecycle + tests reorganisation ([#5](https://github.com/gerket/openproject-mcp-server/issues/5)) ([482101a](https://github.com/gerket/openproject-mcp-server/commit/482101aafd1182d4e928db0be82b85fa48e939d3))
* **tools:** documents, storages, file links, categories, views (14 new tools) ([#7](https://github.com/gerket/openproject-mcp-server/issues/7)) ([f73dca5](https://github.com/gerket/openproject-mcp-server/commit/f73dca563d51eed0cfaac4c5c44bca6621d9c1bf))
* **tools:** principals, placeholder users, user CRUD, preferences + admin tag ([#6](https://github.com/gerket/openproject-mcp-server/issues/6)) ([cf88fb7](https://github.com/gerket/openproject-mcp-server/commit/cf88fb7d6b38852388b812d051f03f370f1e69d0))
* **tools:** queries + profile tags + env-var filtering ([#4](https://github.com/gerket/openproject-mcp-server/issues/4)) ([c8f8579](https://github.com/gerket/openproject-mcp-server/commit/c8f857992a9e13325f718b82015fb535404e7464))
* **tools:** WP sub-resources + category tags on all 86 tools ([#3](https://github.com/gerket/openproject-mcp-server/issues/3)) ([17fda83](https://github.com/gerket/openproject-mcp-server/commit/17fda83f3ce76ff4eeb3a9caf9a8db5894a45472))


### Bug Fixes

* **ci:** guard release workflow to only run when tag is on main ([#23](https://github.com/gerket/openproject-mcp-server/issues/23)) ([588e097](https://github.com/gerket/openproject-mcp-server/commit/588e097facf539b43f805afbb663132b06867e26))
* **ci:** upgrade release-please-action to v5 (node24), drop invalid package-name input ([#28](https://github.com/gerket/openproject-mcp-server/issues/28)) ([af48754](https://github.com/gerket/openproject-mcp-server/commit/af48754aa33134eed0c84e56391d22e161b552bc))
* **deps:** add upper bounds to mcp, aiohttp, and pydantic dependencies ([#26](https://github.com/gerket/openproject-mcp-server/issues/26)) ([8ce84b9](https://github.com/gerket/openproject-mcp-server/commit/8ce84b94c45c386255258c96db30d39b2b946db6))
* **deps:** pin fastmcp to &lt;3.0.0 to avoid breaking API changes ([#25](https://github.com/gerket/openproject-mcp-server/issues/25)) ([77c9611](https://github.com/gerket/openproject-mcp-server/commit/77c96113b1c1857a47f81178372fc9c4b1a176f2))
* **release:** add packages section with include-component-in-tag false ([#34](https://github.com/gerket/openproject-mcp-server/issues/34)) ([49620b5](https://github.com/gerket/openproject-mcp-server/commit/49620b55e90d2e15e23a3e7c9f90379f302fecaa))
* **release:** set manifest version to 3.0.0 to match last tag ([#33](https://github.com/gerket/openproject-mcp-server/issues/33)) ([bfd04a1](https://github.com/gerket/openproject-mcp-server/commit/bfd04a1a98f07509bf5a0bba71722451c9df0a75))


### Documentation

* **docs:** add NOTICE preserving upstream MIT attribution ([1af9cd7](https://github.com/gerket/openproject-mcp-server/commit/1af9cd7cd8dd379e9f56f3a0b3117142de93c706))
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
