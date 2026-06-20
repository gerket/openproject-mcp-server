#!/usr/bin/env python3
"""
Syntax and Structure Validation Test for News Tools.

This test validates:
1. Python syntax correctness
2. File structure
3. Import statements
4. Function/class definitions
"""

import ast
import os
import py_compile
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_syntax_validation():
    """Test Python syntax for all news-related files."""
    files_to_check = ["src/tools/news.py", "src/client.py", "src/utils/formatting.py"]

    for filepath in files_to_check:
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"Syntax error in {filepath}: {e}")


def test_file_structure():
    """Test that required functions and classes exist."""
    # Test news.py structure
    with open("src/tools/news.py", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)

    # Find all function and class definitions
    async_functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            async_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    # Check for required classes
    required_classes = ["CreateNewsInput", "UpdateNewsInput"]
    for cls in required_classes:
        assert cls in classes, f"Class {cls} missing from src/tools/news.py"

    # Check for required async functions (tools)
    required_functions = [
        "list_news",
        "create_news",
        "get_news",
        "update_news",
        "delete_news",
    ]
    for func in required_functions:
        assert (
            func in async_functions
        ), f"Async function {func} missing from src/tools/news.py"

    # Test client.py for news methods
    with open("src/client.py", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)

    all_methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            all_methods.append(node.name)

    required_methods = [
        "get_news",
        "get_news_item",
        "create_news",
        "update_news",
        "delete_news",
    ]
    for method in required_methods:
        assert method in all_methods, f"Method {method} missing from src/client.py"

    # Test formatting.py for news formatting functions
    with open("src/utils/formatting.py", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)

    functions = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]

    required_formatting = ["format_news_list", "format_news_detail"]
    for func in required_formatting:
        assert (
            func in functions
        ), f"Function {func} missing from src/utils/formatting.py"


def test_documentation():
    """Test that integration test setup doc exists."""
    assert os.path.exists(
        "docs/integration-test-setup.md"
    ), "docs/integration-test-setup.md missing"


def test_server_integration():
    """Test that server.py includes news import."""
    with open("src/server.py", encoding="utf-8") as f:
        content = f.read()

    assert (
        "news," in content or "import news" in content
    ), "News import missing in server.py"


def test_docstrings():
    """Test that all tools have proper docstrings."""
    with open("src/tools/news.py", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            docstring = ast.get_docstring(node)
            assert docstring, f"Async function '{node.name}' in src/tools/news.py is missing a docstring"
