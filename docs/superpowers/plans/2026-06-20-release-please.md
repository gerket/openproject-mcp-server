# Release Please Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `release-please.yml` workflow that automates version bumping in `pyproject.toml`, `CHANGELOG.md` maintenance, and GitHub Release tag creation via a merge-controlled Release PR.

**Architecture:** A single new workflow file runs `googleapis/release-please-action@v4` on every push to `main`. It upserts a "Release PR" accumulating conventional commits since the last `v*.*.*` tag. Merging that PR pushes the tag, which fires the existing `release.yml` to build and publish the GitHub Release. No other files are modified.

**Tech Stack:** GitHub Actions, `googleapis/release-please-action@v4`, existing `softprops/action-gh-release@v3` in `release.yml`

## Global Constraints

- `release-type: python` — bumps `version = "..."` in `pyproject.toml`
- `package-name: openproject-mcp-server` — must match the name in `pyproject.toml`
- Workflow runs on push to `main` only
- Permissions: `contents: write`, `pull-requests: write`
- `v3.0.0` tag already exists on `main` — no bootstrap tagging needed
- Do not modify `release.yml`

---

### Task 1: Add release-please workflow

**Files:**
- Create: `.github/workflows/release-please.yml`

**Interfaces:**
- Consumes: nothing
- Produces: a workflow that fires on push to `main`, calls `googleapis/release-please-action@v4`, and creates/updates a Release PR

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/release-please.yml` with this exact content:

```yaml
name: Release Please

on:
  push:
    branches: ["main"]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: python
          package-name: openproject-mcp-server
```

- [ ] **Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release-please.yml'))"
```

Expected: no output (no parse errors).

- [ ] **Step 3: Verify the existing release.yml still runs on tags**

```bash
grep "on:" .github/workflows/release.yml -A3
```

Expected output includes `tags:` and `v*.*.*` — confirm it is unchanged.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release-please.yml
git commit -m "ci: add release-please for automated semver and changelog"
```

- [ ] **Step 5: Push and verify CI**

```bash
git push origin feature/fastmcp3-upgrade
gh pr checks <pr-number>
```

Expected: `Release Please` check does not appear yet (it only runs on pushes to `main`). Existing lint and test checks should pass.
