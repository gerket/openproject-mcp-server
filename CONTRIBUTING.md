# Contributing

## Setup

```bash
git clone https://github.com/gerket/openproject-mcp-server.git
cd openproject-mcp-server
uv sync --dev
uv run pre-commit install
```

## Running tests

```bash
# Unit tests (no server required)
uv run pytest

# Live integration tests (requires a running OpenProject instance)
uv run python scripts/setup_test_project.py   # one-time setup
uv run pytest tests/integration -m integration -v
```

## Adding a tool

1. Find or create the module in `src/tools/` for the API domain
2. Add client methods to `src/client.py` — verify against `GET /api/v3/spec.json` on your instance first
3. Add the `@mcp.tool` decorator with all required tags (see tag convention below)
4. Register the module in `src/server.py`
5. Add unit tests in `tests/unit/` and integration tests in `tests/integration/`

## Tag convention

Every `@mcp.tool` must carry at minimum: `{access, category, tool_name}`.

| Tag type | Values |
|---|---|
| Access | `read`, `write` |
| Category | `work-packages`, `projects`, `queries`, `users`, `time`, `content`, `storage`, `notifications`, `finance`, `reports`, `system` |
| Permission | `admin` — tools requiring OpenProject administrator role |
| Profile | `core` (every session), `situational` (task-specific) |
| Composite | `core-read`, `core-write`, `situational-read`, `situational-write` |

The `test_full_sweep` test in `tests/unit/test_tags.py` enforces that every tool has at least one access tag and one non-access tag.

## Commit style

Conventional commits with a required scope: `feat(scope):`, `fix(scope):`, `chore(scope):`, etc.

For breaking changes, add a `BREAKING CHANGE:` footer in the PR description body:

```
feat(server): remove legacy auth endpoint

BREAKING CHANGE: The /auth/v1 endpoint has been removed. Use /auth/v2 instead.
```

Release Please reads the `BREAKING CHANGE:` footer and produces a major version bump.

**Scopes:**

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

## Before opening a PR

```bash
uv run pytest          # all unit tests must pass
uv run pre-commit run --all-files   # formatting + linting
```
