"""JSON shapes the contract tests expect.

JSONPlaceholder does not publish an OpenAPI document. These schemas are the
expectations a client can rely on: which fields exist, and which JSON type
each field has. ``additionalProperties`` is false so a new, unexpected field
fails the test instead of being ignored.

Coordinates are strings in this API, not numbers. That is easy to miss and
worth locking in.
"""

from __future__ import annotations

from typing import Any

import jsonschema

POST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["userId", "id", "title", "body"],
    "properties": {
        "userId": {"type": "integer"},
        "id": {"type": "integer"},
        "title": {"type": "string", "minLength": 1},
        "body": {"type": "string", "minLength": 1},
    },
}

COMMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["postId", "id", "name", "email", "body"],
    "properties": {
        "postId": {"type": "integer"},
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "minLength": 3},
        "body": {"type": "string", "minLength": 1},
    },
}

USER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "name", "username", "email", "address", "phone", "website", "company"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "username": {"type": "string", "minLength": 1},
        "email": {"type": "string", "minLength": 3},
        "address": {
            "type": "object",
            "additionalProperties": False,
            "required": ["street", "suite", "city", "zipcode", "geo"],
            "properties": {
                "street": {"type": "string"},
                "suite": {"type": "string"},
                "city": {"type": "string"},
                "zipcode": {"type": "string"},
                "geo": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["lat", "lng"],
                    "properties": {
                        "lat": {"type": "string"},
                        "lng": {"type": "string"},
                    },
                },
            },
        },
        "phone": {"type": "string"},
        "website": {"type": "string"},
        "company": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "catchPhrase", "bs"],
            "properties": {
                "name": {"type": "string"},
                "catchPhrase": {"type": "string"},
                "bs": {"type": "string"},
            },
        },
    },
}


def list_of(item_schema: dict[str, Any]) -> dict[str, Any]:
    """A non-empty JSON list whose items match one resource schema."""
    return {"type": "array", "minItems": 1, "items": item_schema}


POST_LIST_SCHEMA = list_of(POST_SCHEMA)
COMMENT_LIST_SCHEMA = list_of(COMMENT_SCHEMA)
USER_LIST_SCHEMA = list_of(USER_SCHEMA)


def assert_schema(instance: object, schema: dict[str, Any], label: str) -> None:
    """Fail the test with a short message when ``instance`` does not match."""
    try:
        jsonschema.validate(instance, schema)
    except jsonschema.ValidationError as exc:
        raise AssertionError(f"{label} did not match the expected schema: {exc.message}") from exc
