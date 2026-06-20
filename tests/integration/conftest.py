"""Shared fixtures for live integration tests.

Run with:
    uv run pytest tests/integration -m integration -v

Required environment variables:
    OPENPROJECT_URL      e.g. https://openproject.thomasgerke.com
    OPENPROJECT_API_KEY  API token for an admin user

Optional:
    OPENPROJECT_PROJECT  project identifier (slug) — defaults to "infrastructure"
    OPENPROJECT_CA_BUNDLE  path to PEM bundle for private CAs
"""

import json
import os

import pytest
import pytest_asyncio

from src.client import OpenProjectClient


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: live tests that require OPENPROJECT_URL and OPENPROJECT_API_KEY",
    )
    config.addinivalue_line(
        "markers",
        "needs_module_time_costs: requires 'Time and costs' module enabled in Administration → Modules. "
        "Set OPENPROJECT_MODULE_TIME_COSTS=1 to run.",
    )
    config.addinivalue_line(
        "markers",
        "needs_module_budgets: requires 'Budgets' module enabled in Administration → Modules. "
        "Set OPENPROJECT_MODULE_BUDGETS=1 to run.",
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip module-gated tests unless the corresponding env var is set."""
    _MODULE_MARKERS = {
        "needs_module_time_costs": "OPENPROJECT_MODULE_TIME_COSTS",
        "needs_module_budgets": "OPENPROJECT_MODULE_BUDGETS",
    }
    for marker_name, env_var in _MODULE_MARKERS.items():
        if item.get_closest_marker(marker_name) and not os.environ.get(env_var):
            pytest.skip(
                f"Requires '{marker_name.replace('needs_module_', '').replace('_', ' ')}' "
                f"module — enable it in Administration → Modules, then set {env_var}=1"
            )


# ---------------------------------------------------------------------------
# Session-level: one client for the whole run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def live_env() -> tuple[str, str]:
    """Return (base_url, api_key) or skip the session if vars are absent."""
    url = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
    key = os.environ.get("OPENPROJECT_API_KEY", "")
    if not url or not key:
        pytest.skip(
            "OPENPROJECT_URL and OPENPROJECT_API_KEY must be set to run integration tests"
        )
    return url, key


@pytest_asyncio.fixture(scope="session")
async def client(live_env: tuple[str, str]) -> OpenProjectClient:
    url, key = live_env
    return OpenProjectClient(base_url=url, api_key=key)


# ---------------------------------------------------------------------------
# Session-level: discover IDs dynamically — never hardcode
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def project_id(client: OpenProjectClient) -> int:
    """Return the ID of the 'infrastructure' project (or OPENPROJECT_PROJECT env var)."""
    slug = os.environ.get("OPENPROJECT_PROJECT", "infrastructure")
    result = await client.get_projects()
    projects = result.get("_embedded", {}).get("elements", [])
    for p in projects:
        if p.get("identifier") == slug:
            return int(p["id"])
    ids = [(p.get("identifier"), p.get("id")) for p in projects]
    pytest.fail(f"Project '{slug}' not found. Available: {ids}")


@pytest_asyncio.fixture(scope="session")
async def wp_type_id(client: OpenProjectClient, project_id: int) -> int:
    """Return the first available work package type ID for the project."""
    result = await client.get_types(project_id)
    types = result.get("_embedded", {}).get("elements", [])
    assert types, "No WP types found for project"
    return int(types[0]["id"])


@pytest_asyncio.fixture(scope="session")
async def activity_id(client: OpenProjectClient) -> int:
    """Return the first available time entry activity ID.

    Only used by tests marked needs_module_time_costs — the marker skips those
    tests before this fixture runs if the module is disabled.
    """
    result = await client.get_time_entry_activities()
    activities = result.get("_embedded", {}).get("elements", [])
    if not activities:
        pytest.skip(
            "No time entry activities configured — add one in Administration → Time and costs"
        )
    return int(activities[0]["id"])


@pytest_asyncio.fixture(scope="session")
async def current_user_id(client: OpenProjectClient) -> int:
    """Return the ID of the authenticated user."""
    result = await client.check_permissions()
    user_id = result.get("id")
    assert user_id, f"check_permissions returned no id: {result}"
    return int(user_id)


@pytest.fixture(scope="session")
def seed_wp_id() -> int | None:
    """Return the ID of the persistent seed WP, or None if not configured.

    Set OPENPROJECT_SEED_WP_ID to the ID created by scripts/setup_test_project.py.
    Tests that require a persistent WP (e.g. custom fields) will skip if not set.
    """
    val = os.environ.get("OPENPROJECT_SEED_WP_ID", "")
    return int(val) if val.isdigit() else None


# ---------------------------------------------------------------------------
# Function-level: fresh WP per test, torn down unconditionally
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def fresh_wp(client: OpenProjectClient, project_id: int, wp_type_id: int) -> int:  # type: ignore[misc]
    """Create a WP, yield its ID, delete it unconditionally in teardown."""
    result = await client.create_work_package(
        {
            "project": project_id,
            "subject": "integration-test-scratch",
            "type": wp_type_id,
        }
    )
    wp_id = result.get("id")
    assert wp_id, f"Failed to create scratch WP: {result}"
    try:
        yield int(wp_id)
    finally:
        try:
            await client.delete_work_package(wp_id)
        except Exception:
            pass  # best-effort; don't mask test failures


# ---------------------------------------------------------------------------
# Helpers available to all test modules
# ---------------------------------------------------------------------------


def extract_elements(result: dict) -> list:
    return result.get("_embedded", {}).get("elements", [])


def project_filter(project_id: int) -> str:
    return json.dumps([{"project": {"operator": "=", "values": [str(project_id)]}}])
