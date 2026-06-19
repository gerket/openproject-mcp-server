"""Unit tests for query client methods (network-free)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.client import OpenProjectClient


@pytest.fixture
def client() -> OpenProjectClient:
    return OpenProjectClient(base_url="https://op.test", api_key="k")


@pytest.mark.asyncio
async def test_get_queries_no_project(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_queries()
        req.assert_called_once_with("GET", "/queries")


@pytest.mark.asyncio
async def test_get_queries_with_project(client):
    mock = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_queries(project_id=4)
        call_endpoint = req.call_args[0][1]
        assert "project_id" in call_endpoint or "filters" in call_endpoint


@pytest.mark.asyncio
async def test_get_query(client):
    mock = {"id": 7, "name": "My query"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.get_query(7)
        req.assert_called_once_with("GET", "/queries/7")
        assert result == mock


@pytest.mark.asyncio
async def test_get_default_query(client):
    mock = {"id": 1, "name": "Default"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_default_query()
        req.assert_called_once_with("GET", "/queries/default")


@pytest.mark.asyncio
async def test_get_default_query_project(client):
    mock = {"id": 2, "name": "Default (project)"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.get_default_query(project_id=4)
        req.assert_called_once_with("GET", "/projects/4/queries/default")


@pytest.mark.asyncio
async def test_create_query(client):
    payload = {"name": "Test", "_links": {}}
    mock = {"id": 9, "name": "Test"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.create_query(payload)
        req.assert_called_once_with("POST", "/queries", payload)
        assert result == mock


@pytest.mark.asyncio
async def test_update_query(client):
    payload = {"name": "Updated"}
    mock = {"id": 9, "name": "Updated"}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        result = await client.update_query(9, payload)
        req.assert_called_once_with("PATCH", "/queries/9", payload)
        assert result == mock


@pytest.mark.asyncio
async def test_delete_query(client):
    with patch.object(client, "_request", new=AsyncMock(return_value={})) as req:
        result = await client.delete_query(9)
        req.assert_called_once_with("DELETE", "/queries/9")
        assert result is True


@pytest.mark.asyncio
async def test_star_query(client):
    mock = {"id": 9, "starred": True}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.star_query(9)
        req.assert_called_once_with("PATCH", "/queries/9/star")


@pytest.mark.asyncio
async def test_unstar_query(client):
    mock = {"id": 9, "starred": False}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock)) as req:
        await client.unstar_query(9)
        req.assert_called_once_with("PATCH", "/queries/9/unstar")
