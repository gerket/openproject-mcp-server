# Release Automation Design — Release Please

Date: 2026-06-20

## Goal

Automate semver version bumping and GitHub Release creation using conventional commits, with a human-controlled ship moment (merging the Release PR).

## How it works

1. Commits land on `main` via merged PRs. PR titles are enforced to follow Conventional Commits format by `pr-title.yml`.
2. On every push to `main`, the `release-please.yml` workflow runs `googleapis/release-please-action`. It reads commits since the last release tag and upserts a single "Release PR" — bumping `version` in `pyproject.toml`, prepending a section to `CHANGELOG.md`, and setting the PR title to `chore(main): release X.Y.Z`.
3. When ready to ship, merge the Release PR. Release Please pushes the tag (e.g. `v3.2.0`).
4. The existing `release.yml` fires on the tag: runs tests, builds dist, creates GitHub Release with generated notes.

## Version bump rules (conventional commits → semver)

| Commit type | Bump |
|-------------|------|
| `feat:` | minor |
| `fix:`, `perf:`, `refactor:` | patch |
| Any type with `!` or `BREAKING CHANGE:` footer | major |
| `chore:`, `docs:`, `ci:`, `test:`, `style:` | none (no release) |

## New file: `.github/workflows/release-please.yml`

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

`release-type: python` tells Release Please to bump `version = "..."` in `pyproject.toml`.

## CHANGELOG.md

Release Please owns `CHANGELOG.md` going forward — it prepends each new release section. The existing hand-written `[3.0.0]` entry is preserved as-is; new entries appear above it.

## Bootstrap

`v3.0.0` tag already exists on `main`. Release Please will use it as the baseline and accumulate commits since then into a `3.1.0` Release PR once this PR merges.

## Out of scope

- PyPI publishing (deferred — GitHub Releases only for now)
- Release Please config file (`release-please-config.json`) — not needed for a single-package Python repo with defaults
