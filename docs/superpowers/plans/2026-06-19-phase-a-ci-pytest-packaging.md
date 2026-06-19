# Phase A: CI + pytest Migration + Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `uv run pytest` the single command that runs all 110 unit tests, gate every PR with GitHub Actions CI, and clean up pyproject.toml so the package is installable and correctly described.

**Architecture:** Three independent workstreams executed sequentially. First a `conftest.py` + `pyproject.toml` pytest config that lets the existing `async def test_*` functions work under pytest with zero per-test changes (pytest-asyncio `auto` mode). Then each `__main__`-style test file gets its `if __name__ == "__main__":` block removed and a stale `print()` progress line stripped. Finally a CI workflow and pyproject.toml cleanup are applied in the same commit.

**Tech Stack:** pytest 8+, pytest-asyncio 0.23+, GitHub Actions, uv, Python 3.10+

## Global Constraints

- Worktree: `/Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/feature-new-api-domains`
- All commands run from the worktree root
- `uv run pytest` must collect ≥110 tests and show 0 failures after every task
- `test_live_integration.py` and `test_tools.py` are excluded from the default pytest run (they require live credentials)
- The 3 already-pytest files (`test_client_retry.py`, `test_client_transitions.py`, `test_client_custom_fields.py`) must continue passing unchanged
- Do NOT change any assertion logic, mock setup, or tool-under-test in any test file — only remove `__main__` boilerplate
- Conventional commit messages; one commit per task
- `pyproject.toml` author: `Tom Gerke <tom@thomasgerke.com>`; version: `2.0.0`

## File map

| File | Action |
|---|---|
| `conftest.py` (new) | Repo-root pytest configuration: set env vars, declare `asyncio_mode` |
| `pyproject.toml` | Add pytest/pytest-asyncio deps, pytest config section, fix author/version/black target |
| `src/server.py` | Add `main()` entrypoint function for `[project.scripts]` |
| 21 `test_*.py` files | Remove `if __name__ == "__main__":` block and trailing `print()` lines |
| `.github/workflows/test.yml` (new) | GitHub Actions CI — install uv, sync deps, run pytest |

---

### Task 1: conftest.py + pyproject.toml pytest config

**Files:**
- Create: `conftest.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `uv run pytest --collect-only` collects all `async def test_*` functions without errors

- [ ] **Step 1: Verify current state — pytest collects nothing**

```bash
cd /Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/feature-new-api-domains
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run pytest --collect-only 2>&1 | tail -5
```

Expected: `no tests ran` or collection errors because `__main__`-style files aren't collected.

- [ ] **Step 2: Add pytest deps to `pyproject.toml`**

In `[project.optional-dependencies]`, replace the existing `dev` block with:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "black>=22.0.0",
    "flake8>=4.0.0",
]
```

- [ ] **Step 3: Add pytest config section to `pyproject.toml`**

Append after the existing `[tool.flake8]` section:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["."]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--ignore=test_live_integration.py --ignore=test_tools.py"
```

- [ ] **Step 4: Create `conftest.py`**

```python
"""Pytest configuration: set required environment variables for all test modules."""

import os

# Set before any src.* imports so OpenProjectClient initialises without error.
os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
```

- [ ] **Step 5: Sync deps**

```bash
uv sync --extra dev
```

- [ ] **Step 6: Verify collection works on already-pytest files**

```bash
uv run pytest test_client_retry.py test_client_transitions.py test_client_custom_fields.py -v 2>&1 | tail -10
```

Expected: `15 passed` (6 + 4 + 5).

- [ ] **Step 7: Commit**

```bash
git add conftest.py pyproject.toml uv.lock
git commit -m "chore(test): add conftest.py and pytest config with asyncio auto mode"
```

---

### Task 2: Migrate __main__-style test files — batch 1 (client + news)

Files in this batch: `test_news_tools.py`, `test_news_validation.py`, `test_news_integration.py`

**Files:**
- Modify: `test_news_tools.py`, `test_news_validation.py`, `test_news_integration.py`

**What to change in each file:**
1. Remove the `if __name__ == "__main__":` block and everything after it
2. Remove any `print("✅ PASSED: ...")` lines inside test functions (pytest captures output; these are noise but not errors — keep them if they're genuinely informative, remove if they're just progress markers)
3. Do NOT add `import pytest` or any decorators — `asyncio_mode = "auto"` handles async tests automatically
4. Do NOT change any assertion, mock, or logic

- [ ] **Step 1: Remove __main__ blocks**

For `test_news_tools.py`: delete from the line `if __name__ == "__main__":` to end of file.

For `test_news_validation.py`: delete from `if __name__ == "__main__":` to end of file.

For `test_news_integration.py`: delete from `if __name__ == "__main__":` to end of file.

- [ ] **Step 2: Verify pytest collects and runs these files**

```bash
uv run pytest test_news_tools.py test_news_validation.py test_news_integration.py -v 2>&1 | tail -15
```

Expected: `9 passed` (3 + 5 + 1).

- [ ] **Step 3: Commit**

```bash
git add test_news_tools.py test_news_validation.py test_news_integration.py
git commit -m "test: migrate news test files to pytest"
```

---

### Task 3: Migrate __main__-style test files — batch 2 (new domain modules)

Files: `test_groups.py`, `test_notifications.py`, `test_attachments.py`, `test_costs.py`, `test_wiki_client.py`, `test_wiki_tools.py`

**Files:**
- Modify: all 6 files above

**What to change:** same as Task 2 — remove `if __name__ == "__main__":` block and everything after it. Do not change assertions or logic.

Additionally, these files currently set env vars at module level with `os.environ.setdefault(...)` or `patch.dict`. With `conftest.py` now setting the env before any imports, the per-file `os.environ.setdefault(...)` lines at module level are redundant but harmless — leave them.

- [ ] **Step 1: Remove __main__ blocks from all 6 files**

In each file, delete from `if __name__ == "__main__":` to end of file.

- [ ] **Step 2: Verify pytest collects and runs these files**

```bash
uv run pytest test_groups.py test_notifications.py test_attachments.py test_costs.py test_wiki_client.py test_wiki_tools.py -v 2>&1 | tail -15
```

Expected: `28 passed` (4 + 7 + 7 + 7 + 1 + 2).

- [ ] **Step 3: Commit**

```bash
git add test_groups.py test_notifications.py test_attachments.py test_costs.py test_wiki_client.py test_wiki_tools.py
git commit -m "test: migrate new domain module test files to pytest"
```

---

### Task 4: Migrate __main__-style test files — batch 3 (tool modules)

Files: `test_connection_tools.py`, `test_projects_tools.py`, `test_users_tools.py`, `test_memberships_tools.py`, `test_work_packages_tools.py`, `test_hierarchy_tools.py`, `test_relations_tools.py`, `test_time_entries_tools.py`, `test_versions_tools.py`, `test_weekly_reports_tools.py`

**Files:**
- Modify: all 10 files above

**What to change:** same pattern — remove `if __name__ == "__main__":` block and everything after it.

Note: these files have a `run_all()` or similar runner function called by `__main__`. Remove both the runner function definition AND the `if __name__` block.

- [ ] **Step 1: Remove __main__ blocks and runner functions**

In each file:
- Delete the `async def run_all():` (or equivalent) function definition
- Delete the `if __name__ == "__main__":` block and everything after it

- [ ] **Step 2: Verify pytest collects and runs all 10 files**

```bash
uv run pytest test_connection_tools.py test_projects_tools.py test_users_tools.py test_memberships_tools.py test_work_packages_tools.py test_hierarchy_tools.py test_relations_tools.py test_time_entries_tools.py test_versions_tools.py test_weekly_reports_tools.py -v 2>&1 | tail -15
```

Expected: `45 passed` (2 + 5 + 5 + 4 + 9 + 4 + 4 + 6 + 3 + 3).

- [ ] **Step 3: Commit**

```bash
git add test_connection_tools.py test_projects_tools.py test_users_tools.py test_memberships_tools.py test_work_packages_tools.py test_hierarchy_tools.py test_relations_tools.py test_time_entries_tools.py test_versions_tools.py test_weekly_reports_tools.py
git commit -m "test: migrate tool module test files to pytest"
```

---

### Task 5: Migrate test_tags.py

**Files:**
- Modify: `test_tags.py`

`test_tags.py` has a large `if __name__ == "__main__":` block that calls every test function explicitly. Remove it. The functions are already named `async def test_*` and will be auto-discovered.

- [ ] **Step 1: Remove __main__ block from `test_tags.py`**

Delete from `if __name__ == "__main__":` to end of file.

- [ ] **Step 2: Verify**

```bash
uv run pytest test_tags.py -v 2>&1 | tail -15
```

Expected: `12 passed`.

- [ ] **Step 3: Run full test suite to confirm nothing regressed**

```bash
uv run pytest -v 2>&1 | tail -20
```

Expected: ≥110 passed, 0 failed. (Exact count may be slightly higher due to `test_news_integration.py` having a nested function.)

- [ ] **Step 4: Commit**

```bash
git add test_tags.py
git commit -m "test: migrate test_tags.py to pytest; full suite now runs via uv run pytest"
```

---

### Task 6: pyproject.toml cleanup + src/server.py entrypoint

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/server.py`

**What to change:**

`pyproject.toml`:
- `authors`: `[{name = "Tom Gerke", email = "tom@thomasgerke.com"}]`
- `version`: `"2.0.0"`
- `[tool.black] target-version`: `['py310', 'py311', 'py312']`
- Add `[project.scripts]` section

`src/server.py`:
- Add `main()` function at bottom (called by the script entrypoint)

- [ ] **Step 1: Update pyproject.toml**

Apply these changes to `pyproject.toml`:

```toml
[project]
name = "openproject-mcp-server"
version = "2.0.0"
description = "A Model Context Protocol (MCP) server for OpenProject API v3 integration"
authors = [
    {name = "Tom Gerke", email = "tom@thomasgerke.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
keywords = ["mcp", "openproject", "api", "project-management"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "fastmcp>=2.0.0",
    "mcp>=1.0.0",
    "aiohttp>=3.8.0",
    "python-dotenv>=1.0.0",
    "certifi>=2022.0.0",
    "pydantic>=2.0.0",
    "uvicorn>=0.24.0",
    "starlette>=0.27.0",
]

[project.scripts]
openproject-mcp = "src.server:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "black>=22.0.0",
    "flake8>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["."]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--ignore=test_live_integration.py --ignore=test_tools.py"
```

- [ ] **Step 2: Add `main()` to `src/server.py`**

Append at the very end of `src/server.py`:

```python

def main() -> None:
    """Stdio entrypoint for `openproject-mcp` CLI script."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the entrypoint loads**

```bash
uv run python -c "from src.server import main; print('main() found:', main)"
```

Expected: `main() found: <function main at 0x...>`

- [ ] **Step 4: Verify full test suite still passes**

```bash
uv run pytest 2>&1 | tail -5
```

Expected: all tests pass, 0 errors.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/server.py uv.lock
git commit -m "chore: bump version to 2.0.0, fix author, add CLI entrypoint, update black target"
```

---

### Task 7: GitHub Actions CI

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Create workflow directory and file**

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest --tb=short -q
        env:
          OPENPROJECT_URL: http://test.example.com
          OPENPROJECT_API_KEY: test-key
```

- [ ] **Step 2: Verify the workflow file is valid YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))" && echo "YAML valid"
```

Expected: `YAML valid`

- [ ] **Step 3: Do a local dry-run confirming the command CI will run**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run pytest --tb=short -q 2>&1 | tail -5
```

Expected: all tests pass, summary line like `110 passed in X.Xs`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add GitHub Actions test workflow (Python 3.10/3.11/3.12)"
```

---

### Task 8: Push and open PR

- [ ] **Step 1: Final full test run**

```bash
uv run pytest -q 2>&1 | tail -5
```

Expected: ≥110 passed, 0 failed.

- [ ] **Step 2: Push branch**

```bash
git push
```

- [ ] **Step 3: Open PR**

```bash
gh pr create \
  --title "chore(phase-a): CI, pytest migration, pyproject.toml cleanup" \
  --body "$(cat <<'EOF'
## Summary

- **pytest migration**: all 110 unit tests now run via `uv run pytest`; previously required running 22 separate scripts manually
- **conftest.py**: sets env vars once for the entire test run; eliminates per-file env setup boilerplate
- **GitHub Actions CI**: runs on every push/PR across Python 3.10/3.11/3.12
- **pyproject.toml**: version 2.0.0, real author, correct black target, `[project.scripts]` entrypoint so `openproject-mcp` works as a CLI command after install
- **src/server.py**: `main()` function added for the script entrypoint

## What was NOT changed

- Zero assertion/logic changes in any test file — only `if __name__ == "__main__":` boilerplate removed
- `test_live_integration.py` and `test_tools.py` excluded from default pytest run (require live credentials)

## Test plan
- [ ] `uv run pytest -q` → ≥110 passed, 0 failed
- [ ] `uv run python -c "from src.server import main; main"` → no import error
- [ ] CI workflow triggers on push and goes green
EOF
)"
```

- [ ] **Step 4: Do NOT merge — stop here and wait for user review**

---

## Self-Review

**Spec coverage:**
- CI workflow ✅ Task 7
- pytest migration for all 21 `__main__`-style files ✅ Tasks 2–5
- `conftest.py` env setup ✅ Task 1
- `pyproject.toml` author/version/black/scripts ✅ Task 6
- `src/server.py` main() entrypoint ✅ Task 6
- `test_live_integration.py` excluded from default run ✅ Task 1 (`addopts`)
- 3 already-pytest files unchanged ✅ (not touched in any task)

**Placeholder scan:** None found — every step has exact code and exact expected output.

**Type consistency:** `main()` defined in Task 6 and referenced in the same task's pyproject.toml `[project.scripts]` entry. No cross-task type dependencies.
