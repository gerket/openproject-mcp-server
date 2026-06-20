"""Shared fixtures for live integration tests.

Run with:
    uv run pytest tests/integration -m integration -v

Configuration is loaded from tests/integration/.env (written by
scripts/setup_test_project.py), with env var overrides taking precedence.
The .env file is gitignored. See docs/integration-test-setup.md for details.
"""

import json
import os
import pathlib

import pytest
import pytest_asyncio

from src.client import OpenProjectClient

# ---------------------------------------------------------------------------
# Load tests/integration/.env if present (env vars take precedence)
# ---------------------------------------------------------------------------

_ENV_FILE = pathlib.Path(__file__).parent / ".env"


def _load_env_file() -> None:
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:  # env var overrides file
            os.environ[key] = value


_load_env_file()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: live tests that require OPENPROJECT_URL and OPENPROJECT_API_KEY",
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
async def current_user_id(client: OpenProjectClient) -> int:
    """Return the ID of the authenticated user."""
    result = await client.check_permissions()
    user_id = result.get("id")
    assert user_id, f"check_permissions returned no id: {result}"
    return int(user_id)


@pytest_asyncio.fixture(scope="session")
async def bot_client(live_env: tuple[str, str]) -> OpenProjectClient | None:
    """Client authenticated as the mcp-test-bot user.

    Requires OPENPROJECT_BOT_API_KEY in the environment (or tests/integration/.env).
    Generate it by logging in as mcp-test-bot and creating an API token at
    User menu → Account settings → Access tokens → + API Token.

    Returns None (causing dependent tests to skip) if the key is absent.
    """
    url, _ = live_env
    bot_key = os.environ.get("OPENPROJECT_BOT_API_KEY", "")
    if not bot_key:
        return None
    return OpenProjectClient(base_url=url, api_key=bot_key)


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
