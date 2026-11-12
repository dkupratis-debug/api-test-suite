"""In-memory stand-in for JSONPlaceholder.

The default test run answers HTTP calls from the JSON files in
``tests/fixtures/`` instead of the network. Those files are a small sample
recorded from the real API (not the full catalog of 100 posts or 500
comments). The rules below follow the behavior the public API documents:

* a list can be filtered with query parameters
* an unknown id returns 404 and ``{}``
* POST, PUT, and DELETE answer successfully but do not change the saved data

Filtering compares the query string to the JSON value as text, which is how
``userId=1`` matches the number ``1``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import responses

from apitests.client import DEFAULT_BASE_URL

_FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict[str, Any]]:
    path = _FIXTURE_DIR / name
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError(f"{path.name} must contain a JSON list")
    return data


# Recorded sample, not the full catalog.
# posts 1 and 2 belong to user 1; post 11 belongs to user 2.
# comments 1 and 2 belong to post 1; comment 6 belongs to post 2.
# users are the public sample records Bret and Antonette.
_COLLECTIONS = {
    "posts": _load("posts.json"),
    "comments": _load("comments.json"),
    "users": _load("users.json"),
}


def install_mocks(
    mocked: responses.RequestsMock,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    """Register mocked routes for every method the client uses.

    ``assert_all_requests_are_fired`` is off because each test calls only one
    or two of the routes we register.
    """
    pattern = re.compile(re.escape(base_url.rstrip("/")) + r"/.*")
    for method in (responses.GET, responses.POST, responses.PUT, responses.DELETE):
        mocked.add_callback(
            method,
            pattern,
            callback=_route,
            content_type="application/json",
        )


def _route(request: Any) -> tuple[int, dict[str, str], str]:
    parts = [part for part in urlparse(request.url).path.split("/") if part]
    method = request.method.upper()
    query = parse_qs(urlparse(request.url).query)

    if not parts or parts[0] not in _COLLECTIONS:
        return _respond(404, {})

    name = parts[0]
    records = _COLLECTIONS[name]

    if method == "GET" and len(parts) == 1:
        return _respond(200, _filter_records(records, query))

    if method == "GET" and len(parts) == 2:
        found = _find(records, parts[1])
        if found is None:
            return _respond(404, {})
        return _respond(200, found)

    # The real API returns an empty list here, including when the post id
    # does not exist. It does not return 404 for this nested path.
    if method == "GET" and len(parts) == 3 and name == "posts" and parts[2] == "comments":
        comments = _COLLECTIONS["comments"]
        matched = [item for item in comments if str(item["postId"]) == parts[1]]
        return _respond(200, matched)

    if method == "POST" and len(parts) == 1:
        # Echo the caller's JSON and assign a new id. Do not store it.
        created = dict(_payload(request))
        created["id"] = _next_id(records)
        return _respond(201, created)

    if method == "PUT" and len(parts) == 2:
        # An unknown id is 404. A known id is echoed and not saved.
        if _find(records, parts[1]) is None:
            return _respond(404, {})
        updated = dict(_payload(request))
        if "id" not in updated and parts[1].isdigit():
            updated["id"] = int(parts[1])
        return _respond(200, updated)

    if method == "DELETE" and len(parts) == 2:
        # Delete answers 200 and {} whether or not the id exists, and the
        # record stays in the fixture data.
        return _respond(200, {})

    return _respond(404, {})


def _filter_records(
    records: list[dict[str, Any]],
    query: dict[str, list[str]],
) -> list[dict[str, Any]]:
    if not query:
        return list(records)
    matched: list[dict[str, Any]] = []
    for record in records:
        if all(_field_matches(record, key, values[0]) for key, values in query.items() if values):
            matched.append(record)
    return matched


def _field_matches(record: dict[str, Any], key: str, expected: str) -> bool:
    if key not in record:
        return False
    return str(record[key]) == expected


def _find(records: list[dict[str, Any]], raw_id: str) -> dict[str, Any] | None:
    for record in records:
        if str(record.get("id")) == raw_id:
            return record
    return None


def _next_id(records: list[dict[str, Any]]) -> int:
    return max(int(record["id"]) for record in records) + 1


def _payload(request: Any) -> dict[str, Any]:
    raw = request.body
    if raw in (None, b"", ""):
        return {}
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("mocked write expected a JSON object")
    return data


def _respond(status: int, payload: object) -> tuple[int, dict[str, str], str]:
    return status, {}, json.dumps(payload)
