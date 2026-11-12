"""Contract checks for /posts.

JSONPlaceholder accepts creates, updates, and deletes, then forgets them.
The write tests check both halves of that: the success response, and a
follow-up read that still shows the original data.
"""

from __future__ import annotations

import pytest

from tests.schemas import POST_LIST_SCHEMA, POST_SCHEMA, assert_schema

_NEW_POST = {
    "title": "qa contract check",
    "body": "written by the test suite",
    "userId": 1,
}

_UPDATED_POST = {
    "id": 1,
    "title": "updated title",
    "body": "updated body",
    "userId": 1,
}


def test_list_posts_matches_schema(client) -> None:
    """GET /posts returns 200 and a list of post objects."""
    response = client.get("/posts")
    assert response.status_code == 200
    assert_schema(response.body, POST_LIST_SCHEMA, "GET /posts")


def test_post_field_types(client) -> None:
    """A post has integer ids and a non-empty string title and body."""
    response = client.get("/posts/1")
    assert response.status_code == 200
    post = response.body
    assert isinstance(post["userId"], int)
    assert isinstance(post["id"], int)
    assert isinstance(post["title"], str) and post["title"]
    assert isinstance(post["body"], str) and post["body"]


def test_get_post_by_id(client) -> None:
    """GET /posts/1 returns the post whose id is 1."""
    response = client.get("/posts/1")
    assert response.status_code == 200
    assert_schema(response.body, POST_SCHEMA, "GET /posts/1")
    assert response.body["id"] == 1
    assert response.body["userId"] == 1


def test_filter_posts_by_user_id(client) -> None:
    """GET /posts?userId=1 returns only posts for that user."""
    filtered = client.get("/posts", params={"userId": 1})
    everyone = client.get("/posts")
    assert filtered.status_code == 200
    assert everyone.status_code == 200
    assert_schema(filtered.body, POST_LIST_SCHEMA, "GET /posts?userId=1")
    assert all(post["userId"] == 1 for post in filtered.body)
    assert len(filtered.body) < len(everyone.body)


def test_unknown_user_filter_returns_empty_list(client) -> None:
    """GET /posts?userId=999999 is 200 and an empty list, not a 404."""
    response = client.get("/posts", params={"userId": 999999})
    assert response.status_code == 200
    assert response.body == []


def test_list_comments_for_a_post(client) -> None:
    """GET /posts/1/comments returns only comments for that post."""
    response = client.get("/posts/1/comments")
    assert response.status_code == 200
    assert response.body
    assert all(comment["postId"] == 1 for comment in response.body)


@pytest.mark.parametrize("missing_id", [0, 999999])
def test_missing_post_returns_404(client, missing_id: int) -> None:
    """GET /posts/{id} returns 404 and {} when that post does not exist."""
    response = client.get(f"/posts/{missing_id}")
    assert response.status_code == 404
    assert response.body == {}


def test_create_post_is_a_fake_write(client) -> None:
    """POST /posts returns 201 and the sent fields, then GET of the new id is 404."""
    created = client.post("/posts", _NEW_POST)
    assert created.status_code == 201
    assert_schema(created.body, POST_SCHEMA, "POST /posts")
    assert created.body["title"] == _NEW_POST["title"]
    assert created.body["body"] == _NEW_POST["body"]
    assert created.body["userId"] == _NEW_POST["userId"]
    assert isinstance(created.body["id"], int)

    fetched = client.get(f"/posts/{created.body['id']}")
    assert fetched.status_code == 404
    assert fetched.body == {}


def test_update_post_is_a_fake_write(client) -> None:
    """PUT /posts/1 echoes the sent JSON, but GET still shows the original title."""
    updated = client.put("/posts/1", _UPDATED_POST)
    assert updated.status_code == 200
    assert_schema(updated.body, POST_SCHEMA, "PUT /posts/1")
    assert updated.body == _UPDATED_POST

    fetched = client.get("/posts/1")
    assert fetched.status_code == 200
    assert fetched.body["title"] != _UPDATED_POST["title"]
    assert fetched.body["id"] == 1


def test_delete_post_is_a_fake_write(client) -> None:
    """DELETE /posts/1 returns 200 and {}, but GET still returns the post."""
    deleted = client.delete("/posts/1")
    assert deleted.status_code == 200
    assert deleted.body == {}

    fetched = client.get("/posts/1")
    assert fetched.status_code == 200
    assert fetched.body["id"] == 1
