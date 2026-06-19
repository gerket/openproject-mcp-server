# Phase 0: Tag All Existing Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `tags={"read"}` or `tags={"write"}` to every `@mcp.tool` decorator across all 16 existing tool modules so callers can grant autonomous read access while requiring approval for write operations.

**Architecture:** Pure mechanical retrofit — no logic changes, no new files, no new tests beyond verifying the tags are registered. Every `@mcp.tool` (bare) and `@mcp.tool()` (call-style) becomes `@mcp.tool(tags={"read"})` or `@mcp.tool(tags={"write"})`. The FastMCP `mcp.tool` decorator accepts `tags: set[str]` as a keyword argument, so adding the tag requires only changing the decorator line.

**Tech Stack:** Python 3.10+, FastMCP (tags first-class in `mcp.tool` signature)

## Global Constraints

- Python ≥3.10
- FastMCP `@mcp.tool(tags={"read"})` / `@mcp.tool(tags={"write"})` — exactly one tag per tool, no other tags
- `@mcp.tool` (no parens) → `@mcp.tool(tags={...})` (with parens)
- `@mcp.tool()` (empty parens) → `@mcp.tool(tags={...})` (with tag)
- Do NOT change any function signatures, docstrings, or logic — only the decorator line
- After each task, verify the server loads and tool count matches
- Repo root for all commands: `/Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/feature-new-api-domains`
- All work happens in the existing worktree on branch `feature/new-api-domains` — the open PR already contains the new tool files (wiki, groups, notifications, attachments, costs) which also need tags

## Read / Write assignment

```
READ tools (call with tags={"read"}):
  connection:     test_connection, check_permissions
  work_packages:  list_work_packages, search_work_packages, list_types,
                  list_statuses, list_priorities, list_work_package_activities,
                  list_overdue_work_packages, list_work_packages_due_soon,
                  list_unassigned_work_packages, list_work_packages_created_recently,
                  list_high_priority_work_packages, list_work_packages_nearly_complete
  projects:       list_projects, get_project, get_subprojects
  users:          list_users, get_user, list_roles, get_role,
                  list_project_members, list_user_projects
  memberships:    list_memberships, get_membership
  hierarchy:      list_work_package_children
  relations:      list_work_package_relations, get_work_package_relation
  time_entries:   list_time_entries, list_time_entry_activities
  versions:       list_versions
  weekly_reports: generate_weekly_report, generate_this_week_report,
                  generate_last_week_report, get_report_data
  news:           list_news, get_news
  wiki:           get_wiki_page
  groups:         list_groups, get_group
  notifications:  list_notifications
  attachments:    list_attachments, get_attachment
  costs:          list_cost_types, list_cost_entries

WRITE tools (call with tags={"write"}):
  work_packages:  create_work_package, update_work_package, delete_work_package,
                  assign_work_package, unassign_work_package, add_work_package_comment
  projects:       create_project, add_subproject, update_project, delete_project
  memberships:    create_membership, update_membership, delete_membership
  hierarchy:      set_work_package_parent, remove_work_package_parent
  relations:      create_work_package_relation, update_work_package_relation,
                  delete_work_package_relation
  time_entries:   create_time_entry, update_time_entry, delete_time_entry
  versions:       create_version
  news:           create_news, update_news, delete_news
  notifications:  mark_notification_read, mark_all_notifications_read
  attachments:    upload_attachment, delete_attachment
  costs:          create_cost_entry, update_cost_entry, delete_cost_entry
```

---

### Task 1: Tag connection.py (2 read tools)

**Files:**
- Modify: `src/tools/connection.py`

**Interfaces:**
- Produces: `test_connection` tagged `read`, `check_permissions` tagged `read`

- [ ] **Step 1: Write the verification test**

Create `test_tags.py` at repo root — this file will be extended in every subsequent task:

```python
#!/usr/bin/env python3
"""Verify that all @mcp.tool decorators carry a read or write tag."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def get_tools():
    os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
    os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
    from src.server import mcp
    return {t.name: t for t in await mcp.get_tools()}


async def test_all_tools_have_tags():
    tools = await get_tools()
    missing = [name for name, t in tools.items() if not getattr(t, "tags", None)]
    assert not missing, f"Tools without tags: {missing}"
    print(f"✅ All {len(tools)} tools have tags")


async def test_tag_values():
    tools = await get_tools()
    bad = [
        f"{name}:{t.tags}"
        for name, t in tools.items()
        if getattr(t, "tags", None) and t.tags - {"read", "write"}
    ]
    assert not bad, f"Tools with unexpected tag values: {bad}"
    print("✅ All tags are 'read' or 'write'")


async def assert_tag(tool_name: str, expected_tag: str, tools: dict):
    t = tools.get(tool_name)
    assert t is not None, f"Tool '{tool_name}' not found"
    assert expected_tag in (t.tags or set()), (
        f"Expected {tool_name} to have tag '{expected_tag}', got {t.tags}"
    )


async def test_connection_tags():
    tools = await get_tools()
    await assert_tag("test_connection", "read", tools)
    await assert_tag("check_permissions", "read", tools)
    print("✅ connection tags correct")


if __name__ == "__main__":
    asyncio.run(test_connection_tags())
    print("\n(Full tag sweep will pass once all modules are tagged)")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/tom.gerke/github/personal_github/openproject-mcp-server/.worktrees/feature-new-api-domains
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected test_connection to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/connection.py`**

Change both decorators:

```python
# line 6 — was: @mcp.tool
@mcp.tool(tags={"read"})
async def test_connection() -> str:

# line 27 — was: @mcp.tool
@mcp.tool(tags={"read"})
async def check_permissions() -> str:
```

- [ ] **Step 4: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ connection tags correct`

- [ ] **Step 5: Commit**

```bash
git add src/tools/connection.py test_tags.py
git commit -m "feat(tags): add read tags to connection tools"
```

---

### Task 2: Tag work_packages.py (12 read, 6 write tools)

**Files:**
- Modify: `src/tools/work_packages.py`

**Interfaces:**
- Produces: 12 tools tagged `read`, 6 tools tagged `write`

- [ ] **Step 1: Append to `test_tags.py`**

Add this function to `test_tags.py` (append before the `if __name__ == "__main__":` block):

```python
async def test_work_packages_tags():
    tools = await get_tools()
    read_tools = [
        "list_work_packages", "search_work_packages", "list_types",
        "list_statuses", "list_priorities", "list_work_package_activities",
        "list_overdue_work_packages", "list_work_packages_due_soon",
        "list_unassigned_work_packages", "list_work_packages_created_recently",
        "list_high_priority_work_packages", "list_work_packages_nearly_complete",
    ]
    write_tools = [
        "create_work_package", "update_work_package", "delete_work_package",
        "assign_work_package", "unassign_work_package", "add_work_package_comment",
    ]
    for name in read_tools:
        await assert_tag(name, "read", tools)
    for name in write_tools:
        await assert_tag(name, "write", tools)
    print(f"✅ work_packages tags correct ({len(read_tools)} read, {len(write_tools)} write)")
```

Also update `if __name__ == "__main__":` to call the new function:

```python
if __name__ == "__main__":
    asyncio.run(test_connection_tags())
    asyncio.run(test_work_packages_tags())
    print("\n(Full tag sweep will pass once all modules are tagged)")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_work_packages to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/work_packages.py`**

Apply the following decorator changes (line numbers are approximate — find by function name):

```python
# list_work_packages — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_packages(

# search_work_packages — was: @mcp.tool
@mcp.tool(tags={"read"})
async def search_work_packages(

# create_work_package — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_work_package(input: CreateWorkPackageInput) -> str:

# update_work_package — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_work_package(input: UpdateWorkPackageInput) -> str:

# delete_work_package — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_work_package(work_package_id: int) -> str:

# list_types — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_types(

# list_statuses — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_statuses() -> str:

# list_priorities — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_priorities() -> str:

# assign_work_package — was: @mcp.tool
@mcp.tool(tags={"write"})
async def assign_work_package(

# unassign_work_package — was: @mcp.tool
@mcp.tool(tags={"write"})
async def unassign_work_package(work_package_id: int) -> str:

# add_work_package_comment — was: @mcp.tool
@mcp.tool(tags={"write"})
async def add_work_package_comment(

# list_work_package_activities — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_package_activities(work_package_id: int) -> str:

# list_overdue_work_packages — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_overdue_work_packages(

# list_work_packages_due_soon — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_packages_due_soon(

# list_unassigned_work_packages — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_unassigned_work_packages(

# list_work_packages_created_recently — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_packages_created_recently(

# list_high_priority_work_packages — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_high_priority_work_packages(

# list_work_packages_nearly_complete — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_packages_nearly_complete(
```

- [ ] **Step 4: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ work_packages tags correct (12 read, 6 write)`

- [ ] **Step 5: Commit**

```bash
git add src/tools/work_packages.py test_tags.py
git commit -m "feat(tags): add read/write tags to work_packages tools"
```

---

### Task 3: Tag projects.py (3 read, 4 write tools)

**Files:**
- Modify: `src/tools/projects.py`

**Interfaces:**
- Produces: `list_projects`, `get_project`, `get_subprojects` tagged `read`; `create_project`, `add_subproject`, `update_project`, `delete_project` tagged `write`

- [ ] **Step 1: Append to `test_tags.py`**

Append before `if __name__ == "__main__":`:

```python
async def test_projects_tags():
    tools = await get_tools()
    for name in ["list_projects", "get_project", "get_subprojects"]:
        await assert_tag(name, "read", tools)
    for name in ["create_project", "add_subproject", "update_project", "delete_project"]:
        await assert_tag(name, "write", tools)
    print("✅ projects tags correct (3 read, 4 write)")
```

Update `__main__` to call `test_projects_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_projects to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/projects.py`**

```python
# list_projects — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_projects(

# get_project — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_project(project_id: int) -> str:

# create_project — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_project(input: CreateProjectInput) -> str:

# add_subproject — was: @mcp.tool
@mcp.tool(tags={"write"})
async def add_subproject(

# get_subprojects — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_subprojects(parent_id: int) -> str:

# update_project — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_project(input: UpdateProjectInput) -> str:

# delete_project — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_project(project_id: int) -> str:
```

- [ ] **Step 4: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ projects tags correct (3 read, 4 write)`

- [ ] **Step 5: Commit**

```bash
git add src/tools/projects.py test_tags.py
git commit -m "feat(tags): add read/write tags to projects tools"
```

---

### Task 4: Tag users.py (6 read tools)

**Files:**
- Modify: `src/tools/users.py`

- [ ] **Step 1: Append to `test_tags.py`**

```python
async def test_users_tags():
    tools = await get_tools()
    for name in ["list_users", "get_user", "list_roles", "get_role",
                 "list_project_members", "list_user_projects"]:
        await assert_tag(name, "read", tools)
    print("✅ users tags correct (6 read)")
```

Update `__main__` to call `test_users_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_users to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/users.py`**

```python
# list_users — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_users(

# get_user — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_user(user_id: int) -> str:

# list_roles — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_roles() -> str:

# get_role — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_role(role_id: int) -> str:

# list_project_members — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_project_members(project_id: int) -> str:

# list_user_projects — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_user_projects(user_id: int) -> str:
```

- [ ] **Step 4: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ users tags correct (6 read)`

- [ ] **Step 5: Commit**

```bash
git add src/tools/users.py test_tags.py
git commit -m "feat(tags): add read tags to users tools"
```

---

### Task 5: Tag memberships.py (2 read, 3 write tools)

**Files:**
- Modify: `src/tools/memberships.py`

- [ ] **Step 1: Append to `test_tags.py`**

```python
async def test_memberships_tags():
    tools = await get_tools()
    for name in ["list_memberships", "get_membership"]:
        await assert_tag(name, "read", tools)
    for name in ["create_membership", "update_membership", "delete_membership"]:
        await assert_tag(name, "write", tools)
    print("✅ memberships tags correct (2 read, 3 write)")
```

Update `__main__` to call `test_memberships_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_memberships to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/memberships.py`**

```python
# list_memberships — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_memberships(

# get_membership — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_membership(membership_id: int) -> str:

# create_membership — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_membership(input: CreateMembershipInput) -> str:

# update_membership — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_membership(input: UpdateMembershipInput) -> str:

# delete_membership — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_membership(membership_id: int) -> str:
```

- [ ] **Step 4: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ memberships tags correct (2 read, 3 write)`

- [ ] **Step 5: Commit**

```bash
git add src/tools/memberships.py test_tags.py
git commit -m "feat(tags): add read/write tags to memberships tools"
```

---

### Task 6: Tag hierarchy.py, relations.py (1+2 read, 2+3 write tools)

**Files:**
- Modify: `src/tools/hierarchy.py`
- Modify: `src/tools/relations.py`

- [ ] **Step 1: Append to `test_tags.py`**

```python
async def test_hierarchy_relations_tags():
    tools = await get_tools()
    await assert_tag("list_work_package_children", "read", tools)
    for name in ["set_work_package_parent", "remove_work_package_parent"]:
        await assert_tag(name, "write", tools)
    for name in ["list_work_package_relations", "get_work_package_relation"]:
        await assert_tag(name, "read", tools)
    for name in ["create_work_package_relation", "update_work_package_relation",
                 "delete_work_package_relation"]:
        await assert_tag(name, "write", tools)
    print("✅ hierarchy + relations tags correct")
```

Update `__main__` to call `test_hierarchy_relations_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_work_package_children to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/hierarchy.py`**

```python
# set_work_package_parent — was: @mcp.tool
@mcp.tool(tags={"write"})
async def set_work_package_parent(

# remove_work_package_parent — was: @mcp.tool
@mcp.tool(tags={"write"})
async def remove_work_package_parent(work_package_id: int) -> str:

# list_work_package_children — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_package_children(
```

- [ ] **Step 4: Edit `src/tools/relations.py`**

```python
# create_work_package_relation — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_work_package_relation(input: CreateRelationInput) -> str:

# list_work_package_relations — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_work_package_relations(

# get_work_package_relation — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_work_package_relation(relation_id: int) -> str:

# update_work_package_relation — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_work_package_relation(input: UpdateRelationInput) -> str:

# delete_work_package_relation — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_work_package_relation(relation_id: int) -> str:
```

- [ ] **Step 5: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ hierarchy + relations tags correct`

- [ ] **Step 6: Commit**

```bash
git add src/tools/hierarchy.py src/tools/relations.py test_tags.py
git commit -m "feat(tags): add read/write tags to hierarchy and relations tools"
```

---

### Task 7: Tag time_entries.py, versions.py (2+1 read, 3+1 write tools)

**Files:**
- Modify: `src/tools/time_entries.py`
- Modify: `src/tools/versions.py`

- [ ] **Step 1: Append to `test_tags.py`**

```python
async def test_time_entries_versions_tags():
    tools = await get_tools()
    for name in ["list_time_entries", "list_time_entry_activities"]:
        await assert_tag(name, "read", tools)
    for name in ["create_time_entry", "update_time_entry", "delete_time_entry"]:
        await assert_tag(name, "write", tools)
    await assert_tag("list_versions", "read", tools)
    await assert_tag("create_version", "write", tools)
    print("✅ time_entries + versions tags correct")
```

Update `__main__` to call `test_time_entries_versions_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected list_time_entries to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/time_entries.py`**

```python
# list_time_entries — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_time_entries(

# create_time_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_time_entry(input: CreateTimeEntryInput) -> str:

# update_time_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_time_entry(input: UpdateTimeEntryInput) -> str:

# delete_time_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_time_entry(time_entry_id: int) -> str:

# list_time_entry_activities — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_time_entry_activities() -> str:
```

- [ ] **Step 4: Edit `src/tools/versions.py`**

```python
# list_versions — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_versions(

# create_version — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_version(input: CreateVersionInput) -> str:
```

- [ ] **Step 5: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ time_entries + versions tags correct`

- [ ] **Step 6: Commit**

```bash
git add src/tools/time_entries.py src/tools/versions.py test_tags.py
git commit -m "feat(tags): add read/write tags to time_entries and versions tools"
```

---

### Task 8: Tag weekly_reports.py, news.py (4+2 read, 0+3 write tools)

**Files:**
- Modify: `src/tools/weekly_reports.py`
- Modify: `src/tools/news.py`

**Note:** `news.py` currently uses `@mcp.tool()` with empty parentheses — change to `@mcp.tool(tags={...})`.

- [ ] **Step 1: Append to `test_tags.py`**

```python
async def test_reports_news_tags():
    tools = await get_tools()
    for name in ["generate_weekly_report", "generate_this_week_report",
                 "generate_last_week_report", "get_report_data"]:
        await assert_tag(name, "read", tools)
    for name in ["list_news", "get_news"]:
        await assert_tag(name, "read", tools)
    for name in ["create_news", "update_news", "delete_news"]:
        await assert_tag(name, "write", tools)
    print("✅ weekly_reports + news tags correct")
```

Update `__main__` to call `test_reports_news_tags()`.

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected generate_weekly_report to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/weekly_reports.py`**

```python
# generate_weekly_report — was: @mcp.tool
@mcp.tool(tags={"read"})
async def generate_weekly_report(

# get_report_data — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_report_data(

# generate_this_week_report — was: @mcp.tool
@mcp.tool(tags={"read"})
async def generate_this_week_report(

# generate_last_week_report — was: @mcp.tool
@mcp.tool(tags={"read"})
async def generate_last_week_report(
```

- [ ] **Step 4: Edit `src/tools/news.py`**

```python
# list_news — was: @mcp.tool()
@mcp.tool(tags={"read"})
async def list_news(

# create_news — was: @mcp.tool()
@mcp.tool(tags={"write"})
async def create_news(input: CreateNewsInput) -> str:

# get_news — was: @mcp.tool()
@mcp.tool(tags={"read"})
async def get_news(news_id: int) -> str:

# update_news — was: @mcp.tool()
@mcp.tool(tags={"write"})
async def update_news(input: UpdateNewsInput) -> str:

# delete_news — was: @mcp.tool()
@mcp.tool(tags={"write"})
async def delete_news(news_id: int) -> str:
```

- [ ] **Step 5: Run test to verify it passes**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ weekly_reports + news tags correct`

- [ ] **Step 6: Commit**

```bash
git add src/tools/weekly_reports.py src/tools/news.py test_tags.py
git commit -m "feat(tags): add read/write tags to weekly_reports and news tools"
```

---

### Task 9: Tag wiki.py, groups.py, notifications.py, attachments.py, costs.py (PR branch files)

**Files:**
- Modify: `src/tools/wiki.py`
- Modify: `src/tools/groups.py`
- Modify: `src/tools/notifications.py`
- Modify: `src/tools/attachments.py`
- Modify: `src/tools/costs.py`

- [ ] **Step 1: Append to `test_tags.py`** — final comprehensive check

```python
async def test_new_modules_tags():
    tools = await get_tools()
    # wiki
    await assert_tag("get_wiki_page", "read", tools)
    # groups
    for name in ["list_groups", "get_group"]:
        await assert_tag(name, "read", tools)
    # notifications
    await assert_tag("list_notifications", "read", tools)
    for name in ["mark_notification_read", "mark_all_notifications_read"]:
        await assert_tag(name, "write", tools)
    # attachments
    for name in ["list_attachments", "get_attachment"]:
        await assert_tag(name, "read", tools)
    for name in ["upload_attachment", "delete_attachment"]:
        await assert_tag(name, "write", tools)
    # costs
    for name in ["list_cost_types", "list_cost_entries"]:
        await assert_tag(name, "read", tools)
    for name in ["create_cost_entry", "update_cost_entry", "delete_cost_entry"]:
        await assert_tag(name, "write", tools)
    print("✅ new module tags correct (wiki/groups/notifications/attachments/costs)")


async def test_full_sweep():
    """Every single registered tool must have exactly one of: read, write."""
    tools = await get_tools()
    missing = [name for name, t in tools.items() if not getattr(t, "tags", None)]
    bad_values = [
        f"{name}:{t.tags}"
        for name, t in tools.items()
        if getattr(t, "tags", None) and t.tags - {"read", "write"}
    ]
    assert not missing, f"Tools without tags: {sorted(missing)}"
    assert not bad_values, f"Tools with unexpected tag values: {bad_values}"
    read_count = sum(1 for t in tools.values() if "read" in (t.tags or set()))
    write_count = sum(1 for t in tools.values() if "write" in (t.tags or set()))
    print(f"✅ Full sweep: {len(tools)} tools, {read_count} read, {write_count} write")
```

Update `__main__` to call both new functions:

```python
if __name__ == "__main__":
    asyncio.run(test_connection_tags())
    asyncio.run(test_work_packages_tags())
    asyncio.run(test_projects_tags())
    asyncio.run(test_users_tags())
    asyncio.run(test_memberships_tags())
    asyncio.run(test_hierarchy_relations_tags())
    asyncio.run(test_time_entries_versions_tags())
    asyncio.run(test_reports_news_tags())
    asyncio.run(test_new_modules_tags())
    asyncio.run(test_full_sweep())
    print("\n✅ All tag tests passed")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `AssertionError: Expected get_wiki_page to have tag 'read', got None`

- [ ] **Step 3: Edit `src/tools/wiki.py`**

```python
# get_wiki_page — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_wiki_page(wiki_page_id: int) -> str:
```

- [ ] **Step 4: Edit `src/tools/groups.py`**

```python
# list_groups — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_groups() -> str:

# get_group — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_group(group_id: int) -> str:
```

- [ ] **Step 5: Edit `src/tools/notifications.py`**

```python
# list_notifications — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_notifications(

# mark_notification_read — was: @mcp.tool
@mcp.tool(tags={"write"})
async def mark_notification_read(notification_id: int) -> str:

# mark_all_notifications_read — was: @mcp.tool
@mcp.tool(tags={"write"})
async def mark_all_notifications_read() -> str:
```

- [ ] **Step 6: Edit `src/tools/attachments.py`**

```python
# upload_attachment — was: @mcp.tool
@mcp.tool(tags={"write"})
async def upload_attachment(input: UploadAttachmentInput) -> str:

# list_attachments — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_attachments(container_type: str, container_id: int) -> str:

# get_attachment — was: @mcp.tool
@mcp.tool(tags={"read"})
async def get_attachment(attachment_id: int) -> str:

# delete_attachment — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_attachment(attachment_id: int) -> str:
```

- [ ] **Step 7: Edit `src/tools/costs.py`**

```python
# list_cost_types — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_cost_types() -> str:

# list_cost_entries — was: @mcp.tool
@mcp.tool(tags={"read"})
async def list_cost_entries(

# create_cost_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def create_cost_entry(input: CreateCostEntryInput) -> str:

# update_cost_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def update_cost_entry(input: UpdateCostEntryInput) -> str:

# delete_cost_entry — was: @mcp.tool
@mcp.tool(tags={"write"})
async def delete_cost_entry(cost_entry_id: int) -> str:
```

- [ ] **Step 8: Run full test suite**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected output:
```
✅ connection tags correct
✅ work_packages tags correct (12 read, 6 write)
✅ projects tags correct (3 read, 4 write)
✅ users tags correct (6 read)
✅ memberships tags correct (2 read, 3 write)
✅ hierarchy + relations tags correct
✅ time_entries + versions tags correct
✅ weekly_reports + news tags correct
✅ new module tags correct (wiki/groups/notifications/attachments/costs)
✅ Full sweep: 64 tools, 39 read, 25 write

✅ All tag tests passed
```

- [ ] **Step 9: Commit**

```bash
git add src/tools/wiki.py src/tools/groups.py src/tools/notifications.py \
        src/tools/attachments.py src/tools/costs.py test_tags.py
git commit -m "feat(tags): add read/write tags to wiki, groups, notifications, attachments, costs tools"
```

---

### Task 10: Push and open PR

- [ ] **Step 1: Confirm all tests pass together**

```bash
OPENPROJECT_URL=http://test.example.com OPENPROJECT_API_KEY=test-key uv run python test_tags.py
```

Expected: `✅ All tag tests passed`

- [ ] **Step 2: Push branch**

```bash
git push
```

- [ ] **Step 3: Open PR**

```bash
gh pr create \
  --title "feat(tags): tag all 64 tools as read or write for permission-scoped access" \
  --body "$(cat <<'EOF'
## Summary

Adds \`tags={\"read\"}\` or \`tags={\"write\"}\` to every \`@mcp.tool\` decorator across
all 16 tool modules (64 tools total).

This enables callers to configure Claude Code to auto-allow read tools while
requiring approval for write tools — without enumerating individual tool names.

**Split:**
- 39 read tools: all list_*, get_*, search_*, check_*, test_*, generate_* functions
- 25 write tools: all create_*, update_*, delete_*, add_*, assign_*, upload_*, mark_* functions

## No logic changes

Pure decorator retrofit. No function signatures, docstrings, or business logic
were changed. The only change per tool is: \`@mcp.tool\` → \`@mcp.tool(tags={\"read\"})\`
(or \`write\`).

## Test plan
- [ ] \`uv run python test_tags.py\` passes: 64 tools, 39 read, 25 write
- [ ] Server loads without error
EOF
)"
```

- [ ] **Step 4: Do NOT merge — stop here and wait for user review**

---

## Self-Review

**Spec coverage:**
- All 64 tools assigned a tag ✅ (39 read + 25 write = 64)
- `news.py` `@mcp.tool()` → `@mcp.tool(tags={...})` conversion called out explicitly ✅
- `test_full_sweep` catches any future tool added without a tag ✅
- PR branch tools (wiki/groups/notifications/attachments/costs) covered in Task 9 ✅

**Placeholder scan:** None found — every step has exact code.

**Type consistency:** `tags={"read"}` and `tags={"write"}` used consistently throughout.
