# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install deps (dev group includes pytest, ruff, mypy, pre-commit)
uv sync --dev

# Unit tests (fast, no live server needed)
uv run pytest --tb=short -q

# Single test
uv run pytest tests/unit/test_connection_tools.py::test_test_connection -v

# Integration tests (requires OPENPROJECT_URL + OPENPROJECT_API_KEY in env or tests/integration/.env)
uv run pytest tests/integration -m integration -v

# Lint + format check
uv run ruff check .
uv run ruff format --check .

# Type check
uv run mypy src/

# Run the server locally (requires .env with OPENPROJECT_URL + OPENPROJECT_API_KEY)
uv run openproject-mcp
```

## uv + git worktrees

uv resolves the project root by walking up from `cwd` looking for `pyproject.toml` — not by git boundaries. When running from a worktree, it will walk up to the repo root and use the root `.venv`, which means you get the wrong Python environment.

**Always pass `--project` when running uv commands in a worktree:**

```bash
# From anywhere — forces uv to use the worktree's own venv
uv --project .worktrees/<name> sync --dev
uv --project .worktrees/<name> run pytest --tb=short -q

# Or cd into the worktree first, then invoke the worktree's venv directly
cd .worktrees/<name>
.venv/bin/python -m pytest --tb=short -q
```

The worktree will have its own `.venv` created by `uv sync` when `--project` points to it. Without this, test runs silently use the root environment and may test against the wrong package versions.

## Architecture

The server is a [FastMCP](https://github.com/jlowin/fastmcp) application. The initialization sequence in `src/server.py` matters:

1. `FastMCP` instance (`mcp`) is created
2. Tag-based filtering is applied via `mcp.enable()` / `mcp.disable()` (driven by `OPENPROJECT_MCP_INCLUDE_TAGS` / `OPENPROJECT_MCP_EXCLUDE_TAGS` env vars)
3. `OpenProjectClient` is instantiated and stored as module-level `_client`
4. All tool modules are imported — the `@mcp.tool` decorators register tools with `mcp` as a side effect of import
5. `mcp.list_tools()` is called once to log the tool count

**Adding a tool:** Create or edit a file in `src/tools/`, decorate the function with `@mcp.tool(tags={...})`, and add the module to the import block in `src/server.py`. Every tool must carry exactly one access tag (`read` or `write`) plus at least one category tag. `test_tags.py` enforces this.

**Tool pattern:** Each tool imports `mcp` and `get_client` from `src.server`. It calls `get_client()` at runtime (not import time) to get the `OpenProjectClient` instance. Tools use Pydantic models for complex inputs and return formatted strings.

**`OpenProjectClient` (`src/client.py`):** Async HTTP client wrapping OpenProject API v3. All API calls go through `_request()`. Handles auth (Basic with API key), optional proxy, optional custom CA bundle, pagination, and custom-field merging for work packages.

**`src/utils/formatting.py`:** Shared helpers that format API responses into markdown strings returned by tools.

## Environment variables

See `env_example.txt` for the full list. Required at runtime: `OPENPROJECT_URL`, `OPENPROJECT_API_KEY`. Unit tests stub these out; integration tests need real values.

## Testing conventions

- **Unit tests** (`tests/unit/`): mock `get_client` at the tool module level (`patch("src.tools.<module>.get_client")`). Set `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` env vars at module top before importing from `src`.
- **Integration tests** (`tests/integration/`): marked `@pytest.mark.integration`, use live fixtures from `conftest.py`. Never hardcode IDs — use the session-scoped fixtures (`project_id`, `wp_type_id`, etc.).
- CI and local both use `uv sync --dev` (dependency-groups key).

## Git workflow

All changes go through worktrees. Never edit files directly on any branch.

```bash
git worktree add .worktrees/<name> -b feature/<name> main
# work, commit
git push -u origin feature/<name>
gh pr create
# after merge:
git pull origin main
git worktree remove .worktrees/<name>
git branch -d feature/<name>
```

`.worktrees/` is gitignored.

**Never enable auto-merge when opening a PR.** PRs must be reviewed and merged manually by the user.

## Commit / PR title style

All PR titles must follow Conventional Commits with a required scope: `type(scope): description`. Enforced by `pr-title.yml`.

| Scope | When to use |
|---|---|
| `server` | FastMCP server init, tag filtering, startup |
| `api` | OpenProject API client (`src/client.py`) |
| `tools` | Any tool module in `src/tools/` |
| `ci` | GitHub Actions workflows |
| `deps` | Dependency bumps, `pyproject.toml`, `uv.lock` |
| `config` | Environment variables, configuration |
| `docs` | README, CONTRIBUTING, CLAUDE.md |
| `tests` | Test suite changes |
| `release` | Release tooling, versioning |
| `auth` | Authentication, API key handling |

Use `feat(scope)!:` or `fix(scope)!:` for breaking changes — Release Please requires the scope to correctly parse the `!` breaking change marker.
