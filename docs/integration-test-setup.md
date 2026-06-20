# Integration Test Setup Guide

Step-by-step instructions for configuring an OpenProject instance to run the
full live integration test suite (`tests/integration/`).

The unit tests (`uv run pytest`) run without any server. The live tests need
a real OpenProject instance with specific projects and admin configuration.
Most setup is automated by `scripts/setup_test_project.py`; this document
covers the click-ops steps that cannot be scripted.

---

## Quick start

```bash
# 1. Run the automated setup script (idempotent — safe to re-run):
export OPENPROJECT_URL=https://your-instance.example.com
export OPENPROJECT_API_KEY=<admin-token>
uv run python scripts/setup_test_project.py

# 2. Work through the click-ops checklist printed by the script.

# 3. Add your API key and bot key to tests/integration/.env (created by the script):
#    OPENPROJECT_API_KEY=<your-admin-token>
#    OPENPROJECT_BOT_API_KEY=<mcp-test-bot-token>

# 4. Run the tests:
uv run pytest tests/integration -m integration -v
```

---

## What the setup script does automatically

`scripts/setup_test_project.py` creates the following via API (idempotent):

- **Test project** (`mcp-test` by default, configurable via `OPENPROJECT_PROJECT`)
- **Seed work package** (`mcp-test-seed`) — persistent WP for tests that need one
- **Test version** (`v1.0-test`) — required for version-type custom field tests
- **Saved query** (`mcp-test-query`) — smoke-test for query tools
- **Bot user** (`mcp-test-bot`) — creates if absent, adds as project member
- **`tests/integration/.env`** — pre-filled with URL, project slug, seed WP ID, and custom action ID

The script also prints a numbered click-ops checklist for everything it cannot automate.

---

## Click-ops checklist

These require the OpenProject web UI. Do each once; they persist across runs.

### 1. Set the bot user's password and generate an API token

The API cannot set passwords for other users.

**a) Set password:**
Administration → Users → `mcp-test-bot` → Edit → Password field → save

**b) Generate token:**
Log in as `mcp-test-bot` at `/login` → User menu → Account settings →
Access tokens → + API Token → copy value

**c) Add to `.env`:**
```
OPENPROJECT_BOT_API_KEY=<token>
```

This enables `test_mark_single_notification_read`: the bot mentions the admin
in a comment, generating a real `mentioned` notification.

### 2. Enable modules on the test project

Projects → `mcp-test` → Settings → Modules → check:
- ☐ Work packages (required)
- ☐ Time and costs (required for `test_time_entries`)
- ☐ Wiki (required for `test_wiki`)
- ☐ News (required for `test_news`)
- ☐ Documents (required for `test_get_document`)

### 3. Create a document in the test project

Projects → `mcp-test` → Documents → + New document (any name, e.g. "Test Document").
Required for `test_get_document`. The Documents module must be enabled first (step 2 above).

### 4. Create a work package category in the test project

Projects → `mcp-test` → **Settings → Work packages → Categories** → + Category (any name, e.g. "Test Category").
Required for `test_get_category`. Note: this is under the project's own Settings, not the global Administration menu.

### 6. Create a budget in the test project

Projects → `mcp-test` → Budgets → + Budget (any name, e.g. "Test Budget").
Required for `test_get_budget`.

### 7. Enable custom fields on the test project

Create missing fields first in Administration → Custom fields → Work packages,
then enable each at Projects → `mcp-test` → Settings → Custom fields.
All fields apply to the Task type.

| Field name | Type |
|---|---|
| `jira_key` | Text (String) |
| `trigger` | Long text |
| `test_bool` | Boolean |
| `test_date` | Date |
| `test_float` | Float |
| `test_int` | Integer |
| `test_link` | URL |
| `test_text` | Text (String) |
| `test_longtext` | Long text |

### 8. Create the 'Start work' custom action (if probe above failed)

Administration → Work packages → Custom actions → + Custom action:
- Name: `Start work`
- Condition: Status = New
- Action: Status → In Progress

After saving, update `OPENPROJECT_CUSTOM_ACTION_ID` in `tests/integration/.env`
with the ID from the URL (`/admin/custom_actions/<ID>/edit`).

### 9. Verify cost types (for `test_costs` — optional)

Administration → Cost types → ensure at least one type is configured.
`GET /cost_types` is not in the OpenProject v3 API spec on standard installs;
these tests skip automatically via the `api_paths` fixture if unavailable.

### 10. Fix attachments storage (for `test_attachment_lifecycle`)

If uploads return 500, the app's storage path is likely misconfigured:
```bash
docker exec <openproject-web-container> ls -la /app/attachments
```
The directory must exist and be writable by the app user.

---

## Running the tests

```bash
# Core suite (all non-module-gated tests):
export OPENPROJECT_API_KEY=<your-token>
uv run pytest tests/integration -m integration -v

# Single module:
uv run pytest tests/integration/test_versions.py -m integration -v

# See available markers:
uv run pytest tests/integration --markers
```

The suite discovers the test project by slug (`OPENPROJECT_PROJECT` env var,
default `mcp-test`) — no hardcoded IDs. Fresh work packages are created and
torn down per test; the only persistent fixtures are the seed WP and the
test project itself.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `SKIPPED — no actions found` | Custom action not created | Follow click-ops step 5 |
| `SKIPPED — OPENPROJECT_BOT_API_KEY not set` | Bot token missing | Follow click-ops step 1 |
| `SKIPPED — No budgets in test project` | No budget created | Follow click-ops step 3 |
| `SKIPPED — GET /cost_types not in API spec` | Plugin-only endpoint | Permanent skip on standard installs |
| Attachment upload 500 | Storage path not writable | Follow click-ops step 7 |
| `401 Unauthorized` | Wrong or expired API token | Re-generate and set `OPENPROJECT_API_KEY` |
| `Project 'mcp-test' not found` | Setup script not run | Run `scripts/setup_test_project.py` first |
