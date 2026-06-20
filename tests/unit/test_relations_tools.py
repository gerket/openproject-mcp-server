#!/usr/bin/env python3
"""Unit tests for relations tools."""

import os
import sys
from unittest.mock import AsyncMock, patch

os.environ.setdefault("OPENPROJECT_URL", "http://test.example.com")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.relations import (
    CreateRelationInput,
    create_work_package_relation,
    delete_work_package_relation,
    list_work_package_relations,
)


async def test_list_relations_empty():
    with patch("src.tools.relations.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.list_work_package_relations = AsyncMock(
            return_value={"_embedded": {"elements": []}}
        )
        mock_get_client.return_value = mock_client
        result = await list_work_package_relations(10)
        assert "Work package #10 has no relations." in result, (
            f"Expected no-relations message, got: {result}"
        )
        print("✅ test_list_relations_empty passed")


async def test_list_relations_results():
    with patch("src.tools.relations.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.list_work_package_relations = AsyncMock(
            return_value={
                "_embedded": {
                    "elements": [
                        {
                            "id": 77,
                            "type": "relates",
                            "_embedded": {
                                "from": {"subject": "WP A", "id": 10},
                                "to": {"subject": "WP B", "id": 11},
                            },
                        }
                    ]
                }
            }
        )
        mock_get_client.return_value = mock_client
        result = await list_work_package_relations(10)
        assert "77" in result, f"Expected relation ID in result, got: {result}"
        assert "relates" in result, f"Expected relation type in result, got: {result}"
        assert "✅" in result, f"Expected success emoji, got: {result}"
        print("✅ test_list_relations_results passed")


async def test_create_relation():
    with patch("src.tools.relations.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.create_work_package_relation = AsyncMock(
            return_value={
                "id": 77,
                "type": "relates",
                "_embedded": {
                    "from": {"subject": "WP A", "id": 10},
                    "to": {"subject": "WP B", "id": 11},
                },
            }
        )
        mock_get_client.return_value = mock_client
        result = await create_work_package_relation(
            CreateRelationInput(from_id=10, to_id=11, type="relates")
        )
        assert "77" in result, f"Expected relation ID in result, got: {result}"
        assert "relates" in result, f"Expected relation type in result, got: {result}"
        assert "**ID**:" in result, f"Expected ID field label in result, got: {result}"
        assert "**Type**:" in result, (
            f"Expected Type field label in result, got: {result}"
        )
        print("✅ test_create_relation passed")


async def test_delete_relation():
    with patch("src.tools.relations.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.delete_work_package_relation = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        result = await delete_work_package_relation(77)
        assert "✅" in result, f"Expected success emoji, got: {result}"
        assert "deleted" in result.lower(), (
            f"Expected 'deleted' in result, got: {result}"
        )
        print("✅ test_delete_relation passed")
