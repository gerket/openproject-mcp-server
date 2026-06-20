"""Unit tests for query tools."""

from unittest.mock import AsyncMock, MagicMock, patch


def _mock_client(responses: dict) -> MagicMock:
    client = MagicMock()
    for method, response in responses.items():
        setattr(client, method, AsyncMock(return_value=response))
    return client


async def test_list_queries_empty():
    mock = _mock_client({"get_queries": {"_embedded": {"elements": []}}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import list_queries

        result = await list_queries()
        assert "no queries" in result.lower() or "0" in result


async def test_list_queries_results():
    queries = [{"id": 1, "name": "Open bugs", "public": False}]
    mock = _mock_client({"get_queries": {"_embedded": {"elements": queries}}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import list_queries

        result = await list_queries()
        assert "Open bugs" in result


async def test_get_query():
    q = {
        "id": 7,
        "name": "My query",
        "public": True,
        "_links": {"project": {"title": "infra"}},
    }
    mock = _mock_client({"get_query": q})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import get_query

        result = await get_query(query_id=7)
        assert "My query" in result
        assert "7" in result


async def test_get_default_query():
    q = {"id": 1, "name": "Default", "public": True, "_links": {}}
    mock = _mock_client({"get_default_query": q})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import get_default_query

        result = await get_default_query()
        assert "Default" in result


async def test_create_query_minimal():
    created = {"id": 9, "name": "Test Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query

        result = await create_query(name="Test Query")
        assert "9" in result or "Test Query" in result
        mock.create_query.assert_called_once()
        payload = mock.create_query.call_args[0][0]
        assert payload["name"] == "Test Query"


async def test_create_query_with_columns_and_sort():
    created = {"id": 10, "name": "Sorted Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query

        result = await create_query(
            name="Sorted Query",
            column_names=["id", "subject", "status"],
            sort_by="updatedAt-desc",
        )
        payload = mock.create_query.call_args[0][0]
        assert payload["_links"]["columns"] == [
            {"href": "/api/v3/queries/columns/id"},
            {"href": "/api/v3/queries/columns/subject"},
            {"href": "/api/v3/queries/columns/status"},
        ]
        assert payload["_links"]["sortBy"] == [
            {"href": "/api/v3/queries/sort_bys/updatedAt-desc"}
        ]


async def test_create_query_with_project():
    created = {"id": 11, "name": "Project Query"}
    mock = _mock_client({"create_query": created})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import create_query

        await create_query(name="Project Query", project_id=4)
        payload = mock.create_query.call_args[0][0]
        assert payload["_links"]["project"] == {"href": "/api/v3/projects/4"}


async def test_update_query():
    updated = {"id": 9, "name": "Renamed"}
    mock = _mock_client({"update_query": updated})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import update_query

        result = await update_query(query_id=9, name="Renamed")
        assert "Renamed" in result or "9" in result
        payload = mock.update_query.call_args[0][1]
        assert payload["name"] == "Renamed"


async def test_delete_query():
    mock = _mock_client({"delete_query": True})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import delete_query

        result = await delete_query(query_id=9)
        assert "deleted" in result.lower()
        mock.delete_query.assert_called_once_with(9)


async def test_star_query():
    mock = _mock_client({"star_query": {"id": 9}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import star_query

        result = await star_query(query_id=9)
        assert "starred" in result.lower()
        mock.star_query.assert_called_once_with(9)


async def test_unstar_query():
    mock = _mock_client({"unstar_query": {"id": 9}})
    with patch("src.tools.queries.get_client", return_value=mock):
        from src.tools.queries import unstar_query

        result = await unstar_query(query_id=9)
        assert "unstarred" in result.lower()
        mock.unstar_query.assert_called_once_with(9)
