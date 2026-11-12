"""A small client for JSONPlaceholder.

JSONPlaceholder (https://jsonplaceholder.typicode.com) is a free fake REST API
used for practice. This client only handles transport: build the URL, send the
request, and turn network problems into a clear error. Deciding whether the
JSON is correct is the test suite's job.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

# The public practice API. Tests that run in live mode call this host.
DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"

# Seconds. Without a timeout, one hung call can stall the whole test run.
DEFAULT_TIMEOUT = 10.0


class ApiError(Exception):
    """The call failed before we had a usable JSON body.

    Timeouts, connection failures, and non-JSON bodies raise this. An HTTP
    status such as 404 does not: the server answered, and the caller should
    read ``status_code`` on the response.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ApiResponse:
    """Status code and parsed JSON from one completed call.

    ``body`` is ``None`` only when the server sends no bytes. JSONPlaceholder's
    404 and delete responses are ``{}``, which is an empty object, not an empty
    body.
    """

    status_code: int
    body: Any


class JsonPlaceholderClient:
    """Calls one JSONPlaceholder-style base URL.

    Pass ``base_url`` to point the same code at a different host. Pass
    ``timeout`` (in seconds) to change how long one call may wait.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("base_url is required")
        # Drop a trailing slash so joining the path never produces "//".
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # A session reuses connections when a test makes several calls.
        self._session = requests.Session()

    def close(self) -> None:
        """Close the connection pool held by this client."""
        self._session.close()

    def __enter__(self) -> JsonPlaceholderClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> ApiResponse:
        """Send GET. ``params`` become the query string, for example userId=1."""
        return self._send("GET", path, params=params)

    def post(self, path: str, payload: dict[str, Any]) -> ApiResponse:
        """Send POST with a JSON body. JSONPlaceholder does not save it."""
        return self._send("POST", path, json=payload)

    def put(self, path: str, payload: dict[str, Any]) -> ApiResponse:
        """Send PUT with a JSON body. JSONPlaceholder echoes it and does not save it."""
        return self._send("PUT", path, json=payload)

    def delete(self, path: str) -> ApiResponse:
        """Send DELETE. JSONPlaceholder returns {} and does not remove the record."""
        return self._send("DELETE", path)

    def _send(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = self._session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.Timeout as exc:
            raise ApiError(f"{method} {url} timed out after {self.timeout} seconds.") from exc
        except requests.RequestException as exc:
            raise ApiError(f"{method} {url} failed: {exc}") from exc
        return ApiResponse(status_code=response.status_code, body=self._read_json(response))

    def _read_json(self, response: requests.Response) -> Any:
        if response.content == b"":
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError(
                f"{response.request.method} {response.url} returned HTTP {response.status_code} "
                "but the body was not JSON.",
                status_code=response.status_code,
            ) from exc
