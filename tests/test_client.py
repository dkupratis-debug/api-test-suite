"""Checks for the client's own error handling.

These tests do not call JSONPlaceholder. They use a fake transport so a
timeout or a bad body can be exercised without the network. They are not
marked live.
"""

from __future__ import annotations

import pytest
import requests
import responses

from apitests.client import DEFAULT_BASE_URL, ApiError, JsonPlaceholderClient


def test_timeout_raises_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A timed-out request raises ApiError and still uses the configured timeout."""
    seen: dict[str, object] = {}

    # The stand-in has to accept the same arguments as Session.request.
    def raise_timeout(self, method, url, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests.Session, "request", raise_timeout)
    with JsonPlaceholderClient(timeout=2) as client:
        with pytest.raises(ApiError, match="timed out") as caught:
            client.get("/posts")
    assert caught.value.status_code is None
    assert seen["timeout"] == 2


def test_connection_error_raises_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A connection failure raises ApiError instead of a raw requests exception."""

    def raise_connection(self, method, url, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(requests.Session, "request", raise_connection)
    with JsonPlaceholderClient() as client:
        with pytest.raises(ApiError, match="network down"):
            client.get("/posts")


def test_non_json_body_raises_api_error() -> None:
    """An HTTP 200 whose body is not JSON raises ApiError."""
    url = f"{DEFAULT_BASE_URL}/posts"
    with responses.RequestsMock() as mocked:
        mocked.add(responses.GET, url, body="<html></html>", status=200, content_type="text/html")
        with JsonPlaceholderClient() as client:
            with pytest.raises(ApiError, match="not JSON") as caught:
                client.get("/posts")
    assert caught.value.status_code == 200


def test_base_url_and_path_join_cleanly() -> None:
    """Extra slashes on the base URL or the path still produce one correct URL."""
    with responses.RequestsMock() as mocked:
        mocked.add(responses.GET, "https://example.test/posts/1", json={"ok": True}, status=200)
        with JsonPlaceholderClient(base_url="https://example.test/") as client:
            response = client.get("/posts/1")
    assert response.status_code == 200
    assert response.body == {"ok": True}
