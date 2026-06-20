"""Unit tests for budget tools."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _mock_client():
    client = MagicMock()
    return client


async def test_list_budgets_with_results():
    budgets = [
        {"id": 1, "subject": "Q2 Budget", "_links": {"project": {"title": "infra"}}},
        {"id": 2, "subject": "Q3 Budget"},
    ]
    mock = _mock_client()
    mock._request = AsyncMock(return_value={"_embedded": {"elements": budgets}})
    with patch("src.tools.costs.get_client", return_value=mock):
        from src.tools.costs import list_budgets

        result = await list_budgets(4)
        assert "Q2 Budget" in result
        assert "Q3 Budget" in result
        assert "✅" in result
        mock._request.assert_called_once_with("GET", "/projects/4/budgets")


async def test_list_budgets_empty():
    mock = _mock_client()
    mock._request = AsyncMock(return_value={"_embedded": {"elements": []}})
    with patch("src.tools.costs.get_client", return_value=mock):
        from src.tools.costs import list_budgets

        result = await list_budgets(4)
        assert "No budgets found" in result


async def test_get_budget():
    budget = {
        "id": 1,
        "subject": "Q2 Budget",
        "_links": {"project": {"title": "infrastructure"}},
    }
    mock = _mock_client()
    mock._request = AsyncMock(return_value=budget)
    with patch("src.tools.costs.get_client", return_value=mock):
        from src.tools.costs import get_budget

        result = await get_budget(1)
        assert "Q2 Budget" in result
        assert "infrastructure" in result
        assert "✅" in result
        mock._request.assert_called_once_with("GET", "/budgets/1")


async def test_get_budget_error():
    mock = _mock_client()
    mock._request = AsyncMock(side_effect=Exception("API Error 404: not found"))
    with patch("src.tools.costs.get_client", return_value=mock):
        from src.tools.costs import get_budget

        result = await get_budget(999)
        assert "Failed" in result
