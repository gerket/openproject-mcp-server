# Changelog

## [5.0.0](https://github.com/gerket/openproject-mcp-server/compare/v4.1.0...v5.0.0) (2026-06-30)


### ⚠ BREAKING CHANGES

* **server:** fastmcp 3.0 removed the include_tags and exclude_tags constructor arguments, changed the mcp.tool decorator to return plain functions instead of FunctionTool wrappers, and replaced the get_tools method with list_tools. All call sites and test patterns were migrated to the new API.

### Features

* **ci:** add lint job (ruff + mypy) and fix lint debt ([#19](https://github.com/gerket/openproject-mcp-server/issues/19)) ([6d62715](https://github.com/gerket/openproject-mcp-server/commit/6d62715eb58b0cd47156aa3575c9b8f04aac4b52))
* **ci:** require scope in all PR titles, force 4.0.0 release ([#31](https://github.com/gerket/openproject-mcp-server/issues/31)) ([4f3a31d](https://github.com/gerket/openproject-mcp-server/commit/4f3a31d5ee5d0ad1e59927080ea4e1daac3bc6ba))
* **docs:** README rewrite for 120-tool state + mark E/F/G complete ([#8](https://github.com/gerket/openproject-mcp-server/issues/8)) ([dd823e3](https://github.com/gerket/openproject-mcp-server/commit/dd823e3a1bb3852371bb839bf9b4499ba8a6879b))
* **server:** new API domains, read/write tags, CI, pytest, pre-commit (Phase 0 + Phase A) ([#2](https://github.com/gerket/openproject-mcp-server/issues/2)) ([6e7312d](https://github.com/gerket/openproject-mcp-server/commit/6e7312d28955cd88ced5d42be8164d0e8d403283))
* **server:** self-hosting enhancements: custom-field values, retry/backoff, custom CA, workflow-aware transitions ([#1](https://github.com/gerket/openproject-mcp-server/issues/1)) ([0a3d8b0](https://github.com/gerket/openproject-mcp-server/commit/0a3d8b09937a9b6be625ac42f148bdb715856693))
* **server:** upgrade to fastmcp 3.x ([#22](https://github.com/gerket/openproject-mcp-server/issues/22)) ([2e8cd36](https://github.com/gerket/openproject-mcp-server/commit/2e8cd3650ab474d38f096c7e19ec6c4dbd2b7596))
* **tools:** add get_work_package tool ([#930](https://github.com/gerket/openproject-mcp-server/issues/930)) ([#52](https://github.com/gerket/openproject-mcp-server/issues/52)) ([41fcd27](https://github.com/gerket/openproject-mcp-server/commit/41fcd27dab71dfb858aebb1d17b89ad9032593dc))
* **tools:** add list_capabilities and describe_tool discovery tools ([#53](https://github.com/gerket/openproject-mcp-server/issues/53)) ([7f42c78](https://github.com/gerket/openproject-mcp-server/commit/7f42c788ed0f0b772049120c5d6a27b365ef8c12))
* **tools:** custom actions + version lifecycle + tests reorganisation ([#5](https://github.com/gerket/openproject-mcp-server/issues/5)) ([482101a](https://github.com/gerket/openproject-mcp-server/commit/482101aafd1182d4e928db0be82b85fa48e939d3))
* **tools:** documents, storages, file links, categories, views (14 new tools) ([#7](https://github.com/gerket/openproject-mcp-server/issues/7)) ([f73dca5](https://github.com/gerket/openproject-mcp-server/commit/f73dca563d51eed0cfaac4c5c44bca6621d9c1bf))
* **tools:** principals, placeholder users, user CRUD, preferences + admin tag ([#6](https://github.com/gerket/openproject-mcp-server/issues/6)) ([cf88fb7](https://github.com/gerket/openproject-mcp-server/commit/cf88fb7d6b38852388b812d051f03f370f1e69d0))
* **tools:** queries + profile tags + env-var filtering ([#4](https://github.com/gerket/openproject-mcp-server/issues/4)) ([c8f8579](https://github.com/gerket/openproject-mcp-server/commit/c8f857992a9e13325f718b82015fb535404e7464))
* **tools:** WP sub-resources + category tags on all 86 tools ([#3](https://github.com/gerket/openproject-mcp-server/issues/3)) ([17fda83](https://github.com/gerket/openproject-mcp-server/commit/17fda83f3ce76ff4eeb3a9caf9a8db5894a45472))


### Bug Fixes

* **api:** wrap bare-string long-text custom fields using form schema ([#50](https://github.com/gerket/openproject-mcp-server/issues/50)) ([71622b5](https://github.com/gerket/openproject-mcp-server/commit/71622b5693b636c775fb1e5cb5b9aa724eb591ff))
* **ci:** guard release workflow to only run when tag is on main ([#23](https://github.com/gerket/openproject-mcp-server/issues/23)) ([28aedc1](https://github.com/gerket/openproject-mcp-server/commit/28aedc1a3443b2b851dec891491e72822a3a557c))
* **ci:** upgrade release-please-action to v5 (node24), drop invalid package-name input ([#28](https://github.com/gerket/openproject-mcp-server/issues/28)) ([e66bc96](https://github.com/gerket/openproject-mcp-server/commit/e66bc967a95bab9bba76b885fe0741a4e777deb7))
* **deps:** add upper bounds to mcp, aiohttp, and pydantic dependencies ([#26](https://github.com/gerket/openproject-mcp-server/issues/26)) ([7752477](https://github.com/gerket/openproject-mcp-server/commit/7752477a4e43fc13717c3d1e17a4e6567fd7729f))
* **deps:** pin fastmcp to &lt;3.0.0 to avoid breaking API changes ([#25](https://github.com/gerket/openproject-mcp-server/issues/25)) ([a2423a2](https://github.com/gerket/openproject-mcp-server/commit/a2423a219fc717c1896b6553656caab4492c3845))
* **release:** add packages section with include-component-in-tag false ([#34](https://github.com/gerket/openproject-mcp-server/issues/34)) ([58686af](https://github.com/gerket/openproject-mcp-server/commit/58686af7f2bbaa14a21ba4c4515f20854a1c50ac))
* **release:** set manifest version to 3.0.0 to match last tag ([#33](https://github.com/gerket/openproject-mcp-server/issues/33)) ([38e1e9b](https://github.com/gerket/openproject-mcp-server/commit/38e1e9b9a4988b2696e7eb06bb40e8ec9ffd3698))
* **release:** set PR title pattern to use release scope ([#48](https://github.com/gerket/openproject-mcp-server/issues/48)) ([9e111f8](https://github.com/gerket/openproject-mcp-server/commit/9e111f818e134aaa165a0711171afcdcc7f0be2c))


### Documentation

* **docs:** add NOTICE preserving upstream MIT attribution ([1af9cd7](https://github.com/gerket/openproject-mcp-server/commit/1af9cd7cd8dd379e9f56f3a0b3117142de93c706))
* **docs:** document BREAKING CHANGE footer convention for major releases ([#46](https://github.com/gerket/openproject-mcp-server/issues/46)) ([116e9fe](https://github.com/gerket/openproject-mcp-server/commit/116e9fe6d527694b85dc576f8c7294e683bdd4b9))
* **docs:** never enable auto-merge when opening a PR ([#35](https://github.com/gerket/openproject-mcp-server/issues/35)) ([4e5a8ae](https://github.com/gerket/openproject-mcp-server/commit/4e5a8aec0e22e6bc1f0ad007cd23145da0663518))

## [4.1.0](https://github.com/gerket/openproject-mcp-server/compare/v4.0.0...v4.1.0) (2026-06-27)


### Features

* **tools:** add get_work_package tool ([#930](https://github.com/gerket/openproject-mcp-server/issues/930)) ([#52](https://github.com/gerket/openproject-mcp-server/issues/52)) ([9a8379f](https://github.com/gerket/openproject-mcp-server/commit/9a8379f2a1c210db3c172fffc43025eef02d897b))
* **tools:** add list_capabilities and describe_tool discovery tools ([#53](https://github.com/gerket/openproject-mcp-server/issues/53)) ([24be632](https://github.com/gerket/openproject-mcp-server/commit/24be6328aaf3ce93ef0312a5c2b5b7196e097bc9))


### Bug Fixes

* **api:** wrap bare-string long-text custom fields using form schema ([#50](https://github.com/gerket/openproject-mcp-server/issues/50)) ([5359309](https://github.com/gerket/openproject-mcp-server/commit/5359309617afc5aef54fc9f0250cb78672da5e85))

## [4.0.0](https://github.com/gerket/openproject-mcp-server/compare/v3.0.0...v4.0.0) (2026-06-20)


### ⚠ BREAKING CHANGES

* **server:** fastmcp 3.0 removed the include_tags and exclude_tags constructor arguments, changed the mcp.tool decorator to return plain functions instead of FunctionTool wrappers, and replaced the get_tools method with list_tools. All call sites and test patterns were migrated to the new API.

### Features

* **ci:** require scope in all PR titles, force 4.0.0 release ([#31](https://github.com/gerket/openproject-mcp-server/issues/31)) ([eef1ca2](https://github.com/gerket/openproject-mcp-server/commit/eef1ca2966c262fbc7f478890222b6e5c3c42f93))
* **server:** upgrade to fastmcp 3.x ([#22](https://github.com/gerket/openproject-mcp-server/issues/22)) ([46329d8](https://github.com/gerket/openproject-mcp-server/commit/46329d8d9064b35bc5854051f9ab3bca8179749f))


### Bug Fixes

* **ci:** upgrade release-please-action to v5 (node24), drop invalid package-name input ([#28](https://github.com/gerket/openproject-mcp-server/issues/28)) ([70a85d0](https://github.com/gerket/openproject-mcp-server/commit/70a85d0467b404471a0c718d7bbfe294f9466eab))
* **release:** add packages section with include-component-in-tag false ([#34](https://github.com/gerket/openproject-mcp-server/issues/34)) ([2a22cda](https://github.com/gerket/openproject-mcp-server/commit/2a22cdaf0d3564ad01fb2396f2a6a94b14309ce8))
* **release:** set manifest version to 3.0.0 to match last tag ([#33](https://github.com/gerket/openproject-mcp-server/issues/33)) ([d080c15](https://github.com/gerket/openproject-mcp-server/commit/d080c15ce02c1b65b666478692ebf4bd08a6db81))
* **release:** set PR title pattern to use release scope ([#48](https://github.com/gerket/openproject-mcp-server/issues/48)) ([1269ad7](https://github.com/gerket/openproject-mcp-server/commit/1269ad71f1caa40ad6d3f05e03659975602f09b9))


### Documentation

* **docs:** document BREAKING CHANGE footer convention for major releases ([#46](https://github.com/gerket/openproject-mcp-server/issues/46)) ([f30b3dd](https://github.com/gerket/openproject-mcp-server/commit/f30b3dd629e338ee37d71d4323819b195f1e4ac3))
* **docs:** never enable auto-merge when opening a PR ([#35](https://github.com/gerket/openproject-mcp-server/issues/35)) ([02384b0](https://github.com/gerket/openproject-mcp-server/commit/02384b04eadd4d45c7911de69c67a8e8424948e6))

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
