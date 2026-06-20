"""Unit tests for src/auth.py — API key auth for HTTP transport."""

import os
from unittest.mock import patch

from src.auth import APIKeyAuth, extract_bearer_token, load_api_keys_from_env


def test_load_api_keys_from_env_empty():
    with patch.dict(os.environ, {"MCP_API_KEYS": ""}, clear=False):
        keys = load_api_keys_from_env()
        assert keys == {}


def test_load_api_keys_from_env_single():
    with patch.dict(os.environ, {"MCP_API_KEYS": "abc123:Alice"}, clear=False):
        keys = load_api_keys_from_env()
        assert keys == {"abc123": "Alice"}


def test_load_api_keys_from_env_multiple():
    with patch.dict(
        os.environ, {"MCP_API_KEYS": "k1:User1,k2:User2,k3:User3"}, clear=False
    ):
        keys = load_api_keys_from_env()
        assert keys == {"k1": "User1", "k2": "User2", "k3": "User3"}


def test_load_api_keys_from_env_strips_whitespace():
    with patch.dict(
        os.environ, {"MCP_API_KEYS": " key1 : Alice , key2 : Bob "}, clear=False
    ):
        keys = load_api_keys_from_env()
        assert "key1" in keys
        assert keys["key1"] == "Alice"


def test_load_api_keys_skips_malformed_entries():
    with patch.dict(
        os.environ, {"MCP_API_KEYS": "good:User,bad_no_colon,another:Fine"}, clear=False
    ):
        keys = load_api_keys_from_env()
        assert "good" in keys
        assert "another" in keys
        assert len(keys) == 2


def test_api_key_auth_validate_valid():
    auth = APIKeyAuth({"secret": "Bob"})
    assert auth.validate("secret") == "Bob"


def test_api_key_auth_validate_invalid():
    auth = APIKeyAuth({"secret": "Bob"})
    assert auth.validate("wrong") is None


def test_api_key_auth_validate_empty():
    auth = APIKeyAuth({})
    assert auth.validate("anything") is None


def test_api_key_auth_loads_from_env():
    with patch.dict(os.environ, {"MCP_API_KEYS": "envkey:EnvUser"}, clear=False):
        auth = APIKeyAuth()
        assert auth.validate("envkey") == "EnvUser"


def test_extract_bearer_token_valid():
    assert extract_bearer_token("Bearer mytoken123") == "mytoken123"


def test_extract_bearer_token_no_bearer():
    assert extract_bearer_token("Basic abc") is None


def test_extract_bearer_token_empty():
    assert extract_bearer_token("") is None


def test_extract_bearer_token_none():
    assert extract_bearer_token(None) is None


def test_extract_bearer_token_bearer_only():
    assert extract_bearer_token("Bearer ") == ""
