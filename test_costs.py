#!/usr/bin/env python3
"""Unit tests for cost types and cost entries."""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_client():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        from src.client import OpenProjectClient
        return OpenProjectClient("http://test.example.com", "test-key")


def _mock_client(method_responses: dict):
    client = MagicMock()
    for method, response in method_responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_get_cost_types_client():
    client = _make_client()
    mock_response = {"_embedded": {"elements": [{"id": 1, "name": "Claude Sonnet Input"}]}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_cost_types()
        mock_req.assert_called_once_with("GET", "/cost_types")
        print("✅ PASSED: get_cost_types client")


async def test_get_cost_entries_filtered():
    client = _make_client()
    mock_response = {"_embedded": {"elements": []}}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.get_cost_entries(work_package_id=5)
        call_endpoint = mock_req.call_args[0][1]
        assert "work_package_id" in call_endpoint or "work_packages" in call_endpoint or "filters" in call_endpoint
        print("✅ PASSED: get_cost_entries filtered by work_package")


async def test_create_cost_entry_client():
    client = _make_client()
    mock_response = {"id": 10, "units": 47382.0}
    with patch.object(client, "_request", new=AsyncMock(return_value=mock_response)) as mock_req:
        result = await client.create_cost_entry({
            "project_id": 1,
            "work_package_id": 5,
            "cost_type_id": 2,
            "units": 47382.0,
            "spent_on": "2026-06-17",
        })
        call_method = mock_req.call_args[0][0]
        assert call_method == "POST"
        assert result == mock_response
        print("✅ PASSED: create_cost_entry client")


async def test_delete_cost_entry_client():
    client = _make_client()
    with patch.object(client, "_request", new=AsyncMock(return_value={})):
        result = await client.delete_cost_entry(10)
        assert result is True
        print("✅ PASSED: delete_cost_entry client")


async def test_list_cost_types_tool():
    types = [{"id": 1, "name": "Claude Sonnet Input", "unit": "tokens", "rate": "0.000003"}]
    mock = _mock_client({"get_cost_types": {"_embedded": {"elements": types}}})
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        with patch("src.tools.costs.get_client", return_value=mock):
            from src.tools.costs import list_cost_types
            result = await list_cost_types.fn()
            assert "Claude Sonnet Input" in result
            print("✅ PASSED: list_cost_types tool")


async def test_create_cost_entry_tool():
    entry = {"id": 10, "units": "47382.00", "spentOn": "2026-06-17"}
    mock = _mock_client({"create_cost_entry": entry})
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        with patch("src.tools.costs.get_client", return_value=mock):
            from src.tools.costs import create_cost_entry, CreateCostEntryInput
            inp = CreateCostEntryInput(
                project_id=1,
                work_package_id=5,
                cost_type_id=2,
                units=47382.0,
                spent_on="2026-06-17",
            )
            result = await create_cost_entry.fn(inp)
            assert "10" in result or "created" in result.lower()
            print("✅ PASSED: create_cost_entry tool")


async def test_create_cost_entry_validation():
    with patch.dict(os.environ, {
        "OPENPROJECT_URL": "http://test.example.com",
        "OPENPROJECT_API_KEY": "test-key",
    }):
        from src.tools.costs import CreateCostEntryInput
        try:
            CreateCostEntryInput(project_id=0, work_package_id=5, cost_type_id=1, units=10.0, spent_on="2026-06-17")
            print("❌ FAILED: should reject project_id=0")
        except Exception:
            print("✅ PASSED: CreateCostEntryInput rejects project_id=0")
        try:
            CreateCostEntryInput(project_id=1, work_package_id=5, cost_type_id=1, units=-1.0, spent_on="2026-06-17")
            print("❌ FAILED: should reject negative units")
        except Exception:
            print("✅ PASSED: CreateCostEntryInput rejects negative units")

