# Integration Test Setup Guide

Step-by-step instructions for configuring an OpenProject instance to run the
full live integration test suite (`tests/test_live_integration.py`).

The unit tests (`uv run pytest`) run without any server. The live tests need
a real OpenProject instance with specific projects, work packages, and admin
configuration in place. This document covers everything.

---

## Prerequisites

- OpenProject instance running and reachable
- Admin account credentials
- API token for the test user (see step 3 below)

---

## Step 1 — Create the test project

1. Log in as admin
2. **Projects → + Project**
3. Name: `infrastructure`
4. Leave all other defaults; save
5. Note the project ID — it is assigned sequentially. On a fresh install it
   will be **4** if you created a few default projects first (the live tests
   use `project_id=4`). If it differs, update the hardcoded `4` values in
   `tests/test_live_integration.py` or add a name-lookup step.

---

## Step 2 — Create the test work package

1. Open the `infrastructure` project
2. **Work packages → + Work package → Task**
3. Subject: `test`
4. Save; note the ID — the live tests target **WP #46** by convention. Update
   `tests/test_live_integration.py` if your instance assigns a different ID.

---

## Step 3 — Create an API token

1. **User menu (top right) → Account settings → Access tokens**
2. **+ API Token**, give it any name, copy the value
3. Set as environment variable before running live tests:
   ```bash
   export OPENPROJECT_URL=https://your-instance.thomasgerke.com
   export OPENPROJECT_API_KEY=<token>
   ```

---

## Step 4 — Custom action setup (required for Phase D tests)

Custom actions are admin-defined workflow buttons that trigger status transitions
or field updates on work packages. The Phase D integration tests
(`custom_actions/list`, `custom_actions/get`, `custom_actions/execute`) require
at least one custom action to exist.

### What "custom actions" are

In OpenProject, a custom action is a button that appears on a work package when
conditions are met (e.g. "status is New"). Clicking it applies a preset change
(e.g. "set status to In Progress"). They are defined by admins as a workflow
shortcut and are surfaced via the `/api/v3/custom_actions` endpoint.

### Creating the test custom action

1. **Administration → Work packages → Custom actions**
   *(If you don't see "Custom actions" in the menu, the Enterprise feature set
   must be enabled. On a self-hosted Community Edition instance, see the
   EnterpriseToken override documented in the homelab ADR-0047.)*

2. Click **+ Custom action**

3. Fill in the form:

   | Field | Value |
   |---|---|
   | **Name** | `Start work` |
   | **Description** | *(optional)* Transitions a task from New to In Progress |

4. Under **Conditions**, add:
   - **Status** = `New`

5. Under **Actions**, add:
   - **Status** → `In Progress`

6. Save.

7. Note the action ID — visible in the URL when you edit it
   (`/admin/custom_actions/<ID>/edit`), or discoverable via
   `list_custom_actions` once the MCP is running.

### How the integration test uses it

`tests/test_live_integration.py` calls `list_custom_actions()` first to
discover whatever action exists (no hardcoded ID). It then:

1. Creates a fresh work package in `New` status
2. Calls `execute_custom_action(action_id, wp_id)`
3. Verifies the work package status changed
4. Deletes the temporary work package

If `list_custom_actions` returns zero actions, the execute test is skipped with
a clear message pointing back to this document.

### Testing manually via the MCP

Once the MCP server is running:

```
list_custom_actions()
# → shows "Start work" (ID: N)

get_custom_action(N)
# → shows name, conditions, actions

execute_custom_action(action_id=N, work_package_id=46)
# → WP #46 transitions from New to In Progress
```

If WP #46 is not in `New` status, the action won't be available (conditions
don't match). Either reset its status to `New` first, or create a fresh WP.

---

## Step 5 — Custom fields (required for full CF test coverage)

The live tests cover custom field read/write for multiple field types.
Create each field below at **Administration → Custom fields → Work packages → + Custom field**.

After creating each field, enable it on the project:
**infrastructure project → Settings → Custom fields → check the field**.

| Field name | Type | Applies to types | Notes |
|---|---|---|---|
| `jira_key` | Text | Task, Epic, Bug | CF2 on a fresh install |
| `trigger` | Long text | Task, Epic, Bug | CF3 |
| `test_boolean` | Boolean | Task | CF4 |
| `test_date` | Date | Task | CF5 |
| `test_float` | Float | Task | CF6 |
| `test_integer` | Integer | Task | CF8 |
| `test_link` | URL | Task | CF9 |
| `test_text` | Text | Task | CF11 |
| `test_long_text` | Long text | Task | CF15 |
| `test_list` | List | Task | CF10 — add options "Option A", "Option B" |
| `test_user` | User | Task | CF12 — add the test user to the project as Member |
| `test_version` | Version | Task | CF13 — project must have at least one version |
| `test_hierarchy` | Hierarchy | Task | CF7 — add root item "Item A" |
| `test_weighted_item_list` | Hierarchy | Task | CF14 — add root item "Item B" |

The CF IDs (`CF2`, `CF3`, …) are assigned sequentially. If your instance assigns
different IDs, update the corresponding `customField<N>` keys in
`tests/test_live_integration.py`.

---

## Step 6 — Enable modules for Phase F tests (budgets, costs)

1. **Administration → Modules**
2. Enable **Time and costs** and **Budgets**

---

## Running the live test suite

```bash
OPENPROJECT_URL=https://your-instance.thomasgerke.com \
OPENPROJECT_API_KEY=<token> \
uv run python tests/test_live_integration.py
```

Expected output ends with `All tests passed!`. Any skipped tests print a
reason; skips caused by missing admin config point back to the relevant section
of this document.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `custom_actions/list: count=0` | No custom action created | Follow Step 4 |
| `custom_actions/execute: Action not applicable` | WP is not in `New` status | Reset WP status to `New` or create a fresh WP |
| `versions/lifecycle_delete: 422` | WPs are assigned to the version | Unassign WPs first, then delete |
| CF tests fail with "field not present in response" | CF not enabled for the project | Enable in project → Settings → Custom fields |
| `401 Unauthorized` | Wrong or expired API token | Re-generate and re-export `OPENPROJECT_API_KEY` |
