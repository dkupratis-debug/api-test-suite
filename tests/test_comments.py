"""Contract checks for /comments."""

from __future__ import annotations

import pytest

from tests.schemas import COMMENT_LIST_SCHEMA, COMMENT_SCHEMA, assert_schema

_NEW_COMMENT = {
    "postId": 1,
    "name": "qa contract check",
    "email": "qa@example.com",
    "body": "written by the test suite",
}


def test_list_comments_matches_schema(client) -> None:
    """GET /comments returns 200 and a list of comment objects."""
    response = client.get("/comments")
    assert response.status_code == 200
    assert_schema(response.body, COMMENT_LIST_SCHEMA, "GET /comments")


def test_comment_field_types(client) -> None:
    """A comment has integer ids and string name, email, and body."""
    response = client.get("/comments/1")
    assert response.status_code == 200
    comment = response.body
    assert isinstance(comment["postId"], int)
    assert isinstance(comment["id"], int)
    assert isinstance(comment["name"], str) and comment["name"]
    assert isinstance(comment["email"], str) and "@" in comment["email"]
    assert isinstance(comment["body"], str) and comment["body"]


def test_get_comment_by_id(client) -> None:
    """GET /comments/1 returns the comment whose id is 1."""
    response = client.get("/comments/1")
    assert response.status_code == 200
    assert_schema(response.body, COMMENT_SCHEMA, "GET /comments/1")
    assert response.body["id"] == 1
    assert response.body["postId"] == 1


def test_filter_comments_by_post_id(client) -> None:
    """GET /comments?postId=1 returns only comments for that post."""
    filtered = client.get("/comments", params={"postId": 1})
    everyone = client.get("/comments")
    assert filtered.status_code == 200
    assert everyone.status_code == 200
    assert_schema(filtered.body, COMMENT_LIST_SCHEMA, "GET /comments?postId=1")
    assert all(comment["postId"] == 1 for comment in filtered.body)
    assert len(filtered.body) < len(everyone.body)


@pytest.mark.parametrize("missing_id", [0, 999999])
def test_missing_comment_returns_404(client, missing_id: int) -> None:
    """GET /comments/{id} returns 404 and {} when that comment does not exist."""
    response = client.get(f"/comments/{missing_id}")
    assert response.status_code == 404
    assert response.body == {}


def test_create_comment_is_a_fake_write(client) -> None:
    """POST /comments returns 201 and the sent fields, then GET of the new id is 404."""
    created = client.post("/comments", _NEW_COMMENT)
    assert created.status_code == 201
    assert_schema(created.body, COMMENT_SCHEMA, "POST /comments")
    assert created.body["postId"] == _NEW_COMMENT["postId"]
    assert created.body["name"] == _NEW_COMMENT["name"]
    assert created.body["email"] == _NEW_COMMENT["email"]
    assert created.body["body"] == _NEW_COMMENT["body"]
    assert isinstance(created.body["id"], int)

    fetched = client.get(f"/comments/{created.body['id']}")
    assert fetched.status_code == 404
    assert fetched.body == {}
