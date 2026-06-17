"""Unit tests for OpenProjectClient retry/backoff + custom-field payload logic.

Network-free: aiohttp.ClientSession.request is monkeypatched with a fake that
returns scripted responses, and asyncio.sleep is patched to record (not wait on)
backoff delays. Run: uv run pytest test_client_retry.py
"""

import asyncio
import json
from contextlib import asynccontextmanager

import pytest

from src.client import OpenProjectClient


class _FakeResponse:
    def __init__(self, status, body="", headers=None):
        self.status = status
        self._body = body if isinstance(body, str) else json.dumps(body)
        self.headers = headers or {}

    async def text(self):
        return self._body


class _FakeSession:
    """Returns queued responses in order; records each request's kwargs."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    @asynccontextmanager
    async def request(self, **kwargs):
        self.calls.append(kwargs)
        yield self._responses.pop(0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _client():
    return OpenProjectClient(base_url="https://op.test", api_key="k")


def _patch(monkeypatch, session, sleeps):
    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda *a, **k: session
    )
    monkeypatch.setattr("aiohttp.TCPConnector", lambda *a, **k: None)

    async def _fake_sleep(d):
        sleeps.append(d)

    monkeypatch.setattr("asyncio.sleep", _fake_sleep)


def test_retries_on_429_then_succeeds(monkeypatch):
    sleeps = []
    session = _FakeSession([
        _FakeResponse(429, headers={"Retry-After": "7"}),
        _FakeResponse(200, {"ok": True}),
    ])
    _patch(monkeypatch, session, sleeps)

    result = asyncio.run(_client()._request("GET", "/x"))

    assert result == {"ok": True}
    assert len(session.calls) == 2          # retried once
    assert sleeps == [7.0]                   # honored Retry-After, not backoff


def test_retries_on_500_with_exponential_backoff(monkeypatch):
    sleeps = []
    session = _FakeSession([
        _FakeResponse(500),
        _FakeResponse(503),
        _FakeResponse(200, {"ok": 1}),
    ])
    _patch(monkeypatch, session, sleeps)

    result = asyncio.run(_client()._request("GET", "/x"))

    assert result == {"ok": 1}
    assert sleeps == [1.0, 2.0]              # base * 2**attempt, no Retry-After


def test_4xx_not_retried(monkeypatch):
    sleeps = []
    session = _FakeSession([_FakeResponse(422, {"message": "bad"})])
    _patch(monkeypatch, session, sleeps)

    with pytest.raises(Exception):
        asyncio.run(_client()._request("POST", "/x", {"a": 1}))

    assert len(session.calls) == 1          # no retry on client error
    assert sleeps == []


def test_gives_up_after_max_retries(monkeypatch):
    sleeps = []
    session = _FakeSession([_FakeResponse(503) for _ in range(OpenProjectClient._MAX_RETRIES)])
    _patch(monkeypatch, session, sleeps)

    with pytest.raises(Exception):
        asyncio.run(_client()._request("GET", "/x"))

    assert len(session.calls) == OpenProjectClient._MAX_RETRIES
    assert len(sleeps) == OpenProjectClient._MAX_RETRIES - 1


def test_retry_delay_prefers_retry_after_header():
    # numeric Retry-After wins
    assert OpenProjectClient._retry_delay(2, {"Retry-After": "11"}) == 11.0
    # non-numeric (HTTP-date) falls back to exponential
    assert OpenProjectClient._retry_delay(0, {"Retry-After": "Wed, 21 Oct 2099 07:28:00 GMT"}) == 1.0
    # no header → exponential
    assert OpenProjectClient._retry_delay(3, None) == 8.0
