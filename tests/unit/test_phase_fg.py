"""Unit tests for Phase F+G tools: documents, storages, file links, categories, views."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.tools.categories import get_category, list_categories
from src.tools.documents import get_document, list_documents, update_document
from src.tools.storages import (
    create_file_links,
    delete_file_link,
    get_file_link,
    get_storage,
    list_project_storages,
    list_storages,
    list_work_package_file_links,
)
from src.tools.views import get_view, list_views

list_documents = list_documents.fn
get_document = get_document.fn
update_document = update_document.fn
list_storages = list_storages.fn
get_storage = get_storage.fn
list_project_storages = list_project_storages.fn
list_work_package_file_links = list_work_package_file_links.fn
get_file_link = get_file_link.fn
create_file_links = create_file_links.fn
delete_file_link = delete_file_link.fn
list_categories = list_categories.fn
get_category = get_category.fn
list_views = list_views.fn
get_view = get_view.fn

from src.tools.documents import UpdateDocumentInput
from src.tools.storages import CreateFileLinksInput

# ── documents ─────────────────────────────────────────────────────────────────


async def test_list_documents_empty():
    with patch("src.tools.documents.get_client") as m:
        c = AsyncMock()
        c.get_documents = AsyncMock(return_value={"_embedded": {"elements": []}})
        m.return_value = c
        result = await list_documents()
        assert "No documents" in result


async def test_list_documents_results():
    docs = [{"id": 1, "title": "Spec Doc", "description": {"raw": "Some text"}}]
    with patch("src.tools.documents.get_client") as m:
        c = AsyncMock()
        c.get_documents = AsyncMock(return_value={"_embedded": {"elements": docs}})
        m.return_value = c
        result = await list_documents()
        assert "Spec Doc" in result
        assert "✅" in result


async def test_get_document():
    with patch("src.tools.documents.get_client") as m:
        c = AsyncMock()
        c.get_document = AsyncMock(
            return_value={
                "id": 1,
                "title": "Spec Doc",
                "description": {"raw": "Details"},
            }
        )
        m.return_value = c
        result = await get_document(1)
        assert "Spec Doc" in result
        assert "Details" in result


async def test_update_document():
    with patch("src.tools.documents.get_client") as m:
        c = AsyncMock()
        c.update_document = AsyncMock(return_value={"id": 1, "title": "Updated"})
        m.return_value = c
        result = await update_document(
            UpdateDocumentInput(document_id=1, title="Updated")
        )
        assert "Updated" in result
        assert "✅" in result


# ── storages ──────────────────────────────────────────────────────────────────


async def test_list_storages_empty():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_storages = AsyncMock(return_value={"_embedded": {"elements": []}})
        m.return_value = c
        result = await list_storages()
        assert "No file storages" in result


async def test_list_storages_results():
    storages = [
        {"id": 1, "name": "OneDrive", "_links": {"type": {"title": "OneDrive"}}}
    ]
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_storages = AsyncMock(return_value={"_embedded": {"elements": storages}})
        m.return_value = c
        result = await list_storages()
        assert "OneDrive" in result
        assert "✅" in result


async def test_list_work_package_file_links_empty():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_work_package_file_links = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        m.return_value = c
        result = await list_work_package_file_links(42)
        assert "No file links" in result


async def test_get_storage():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_storage = AsyncMock(
            return_value={
                "id": 1,
                "name": "OneDrive",
                "_links": {"type": {"title": "OneDrive"}},
            }
        )
        m.return_value = c
        result = await get_storage(1)
        assert "OneDrive" in result
        assert "✅" in result


async def test_list_project_storages_empty():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_project_storages = AsyncMock(return_value={"_embedded": {"elements": []}})
        m.return_value = c
        result = await list_project_storages()
        assert "No project-storage links" in result


async def test_get_file_link():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.get_file_link = AsyncMock(
            return_value={
                "id": 5,
                "originData": {
                    "name": "report.pdf",
                    "mimeType": "application/pdf",
                    "fileSize": 12345,
                },
                "_links": {"storage": {"title": "OneDrive"}},
            }
        )
        m.return_value = c
        result = await get_file_link(5)
        assert "report.pdf" in result
        assert "application/pdf" in result
        assert "OneDrive" in result
        assert "✅" in result


async def test_create_file_links_no_storage():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.create_file_links = AsyncMock(side_effect=Exception("API Error 404"))
        m.return_value = c
        result = await create_file_links(
            CreateFileLinksInput(
                work_package_id=42,
                storage_id=1,
                files=[{"name": "doc.pdf", "originId": "abc123"}],
            )
        )
        assert "not found" in result.lower() or "storage" in result.lower()


async def test_delete_file_link():
    with patch("src.tools.storages.get_client") as m:
        c = AsyncMock()
        c.delete_file_link = AsyncMock(return_value=True)
        m.return_value = c
        result = await delete_file_link(7)
        assert "deleted" in result.lower()
        assert "✅" in result


# ── categories ────────────────────────────────────────────────────────────────


async def test_list_categories_empty():
    with patch("src.tools.categories.get_client") as m:
        c = AsyncMock()
        c.get_project_categories = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        m.return_value = c
        result = await list_categories(4)
        assert "No categories" in result


async def test_list_categories_results():
    cats = [{"id": 1, "name": "Backend"}, {"id": 2, "name": "Frontend"}]
    with patch("src.tools.categories.get_client") as m:
        c = AsyncMock()
        c.get_project_categories = AsyncMock(
            return_value={"_embedded": {"elements": cats}}
        )
        m.return_value = c
        result = await list_categories(4)
        assert "Backend" in result
        assert "Frontend" in result
        assert "✅" in result


async def test_get_category():
    with patch("src.tools.categories.get_client") as m:
        c = AsyncMock()
        c.get_category = AsyncMock(
            return_value={
                "id": 1,
                "name": "Backend",
                "_links": {"project": {"title": "infra"}},
            }
        )
        m.return_value = c
        result = await get_category(1)
        assert "Backend" in result
        assert "infra" in result


# ── views ─────────────────────────────────────────────────────────────────────


async def test_list_views_empty():
    with patch("src.tools.views.get_client") as m:
        c = AsyncMock()
        c.get_views = AsyncMock(return_value={"_embedded": {"elements": []}})
        m.return_value = c
        result = await list_views()
        assert "No views" in result


async def test_list_views_results():
    views = [
        {
            "id": 1,
            "name": "All Open",
            "public": True,
            "starred": False,
            "_links": {"viewType": {"title": "Table"}},
        },
    ]
    with patch("src.tools.views.get_client") as m:
        c = AsyncMock()
        c.get_views = AsyncMock(return_value={"_embedded": {"elements": views}})
        m.return_value = c
        result = await list_views()
        assert "All Open" in result
        assert "Table" in result
        assert "✅" in result


async def test_get_view():
    with patch("src.tools.views.get_client") as m:
        c = AsyncMock()
        c.get_view = AsyncMock(
            return_value={
                "id": 1,
                "name": "All Open",
                "public": True,
                "starred": True,
                "_links": {
                    "viewType": {"title": "Table"},
                    "query": {"title": "Open WPs"},
                },
            }
        )
        m.return_value = c
        result = await get_view(1)
        assert "All Open" in result
        assert "Table" in result
        assert "Open WPs" in result
