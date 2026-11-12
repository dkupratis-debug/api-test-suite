"""Shared fixtures for mocked and live runs.

Every contract test asks for the ``client`` fixture. Pytest then runs that
test twice:

* ``mock`` (default): the ``responses`` library answers from tests/fixtures,
  so CI does not need the network.
* ``live``: the same test calls https://jsonplaceholder.typicode.com.

The live copy is marked ``live`` and skipped unless you opt in with
``pytest --live`` or ``API_TEST_LIVE=1``.
"""

from __future__ import annotations

import os

import pytest
import responses

from apitests.client import JsonPlaceholderClient
from tests.mock_api import install_mocks

_TRUTHY = {"1", "true", "yes"}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Also run live tests against https://jsonplaceholder.typicode.com",
    )


def live_enabled(config: pytest.Config) -> bool:
    """True when this process was asked to call the real API."""
    if config.getoption("--live"):
        return True
    return os.environ.get("API_TEST_LIVE", "").strip().lower() in _TRUTHY


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "client" not in metafunc.fixturenames:
        return
    metafunc.parametrize(
        "client",
        [
            pytest.param("mock", id="mock"),
            pytest.param("live", id="live", marks=pytest.mark.live),
        ],
        indirect=True,
    )


@pytest.fixture
def client(request: pytest.FixtureRequest):
    """Yield a client backed by the mock or by the real API."""
    mode = request.param
    if mode == "live" and not live_enabled(request.config):
        pytest.skip("live checks are off. Pass --live or set API_TEST_LIVE=1.")
    if mode not in {"mock", "live"}:
        raise AssertionError(f"unknown client mode {mode!r}")

    api = JsonPlaceholderClient()
    try:
        if mode == "mock":
            with responses.RequestsMock(assert_all_requests_are_fired=False) as mocked:
                install_mocks(mocked)
                yield api
        else:
            yield api
    finally:
        api.close()
