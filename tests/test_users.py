"""Contract checks for /users.

User records are nested. The interesting contract detail is that
``address.geo.lat`` and ``lng`` are strings, not numbers.
"""

from __future__ import annotations

import pytest

from tests.schemas import USER_LIST_SCHEMA, USER_SCHEMA, assert_schema


def test_list_users_matches_schema(client) -> None:
    """GET /users returns 200 and a list of user objects."""
    response = client.get("/users")
    assert response.status_code == 200
    assert_schema(response.body, USER_LIST_SCHEMA, "GET /users")


def test_user_field_types(client) -> None:
    """A user has string contact fields, and geo coordinates are strings too."""
    response = client.get("/users/1")
    assert response.status_code == 200
    user = response.body
    assert isinstance(user["id"], int)
    assert isinstance(user["name"], str) and user["name"]
    assert isinstance(user["username"], str) and user["username"]
    assert isinstance(user["email"], str) and "@" in user["email"]
    assert isinstance(user["phone"], str) and user["phone"]
    assert isinstance(user["website"], str) and user["website"]
    address = user["address"]
    assert isinstance(address["street"], str) and address["street"]
    assert isinstance(address["city"], str) and address["city"]
    assert isinstance(address["zipcode"], str) and address["zipcode"]
    assert isinstance(address["geo"]["lat"], str) and address["geo"]["lat"]
    assert isinstance(address["geo"]["lng"], str) and address["geo"]["lng"]
    assert isinstance(user["company"]["name"], str) and user["company"]["name"]


def test_get_user_by_id(client) -> None:
    """GET /users/1 returns the sample user whose id is 1."""
    response = client.get("/users/1")
    assert response.status_code == 200
    assert_schema(response.body, USER_SCHEMA, "GET /users/1")
    assert response.body["id"] == 1
    assert response.body["username"] == "Bret"


def test_filter_users_by_username(client) -> None:
    """GET /users?username=Bret returns that one sample user."""
    response = client.get("/users", params={"username": "Bret"})
    assert response.status_code == 200
    assert len(response.body) == 1
    assert_schema(response.body[0], USER_SCHEMA, "GET /users?username=Bret")
    assert response.body[0]["id"] == 1
    assert response.body[0]["username"] == "Bret"


@pytest.mark.parametrize("missing_id", [0, 999999])
def test_missing_user_returns_404(client, missing_id: int) -> None:
    """GET /users/{id} returns 404 and {} when that user does not exist."""
    response = client.get(f"/users/{missing_id}")
    assert response.status_code == 404
    assert response.body == {}
