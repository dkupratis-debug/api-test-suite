# API Test Suite

Portfolio project by David Kupratis for support engineering, QA, tooling, and automation: contract tests for the public [JSONPlaceholder](https://jsonplaceholder.typicode.com) API, so status codes, field types, filters, missing ids, and documented fake writes can be re-run locally and in CI.

## What the tests check, and why

JSONPlaceholder is a free public REST API for practice. When a client and an API stop agreeing, the useful questions are specific. Did the status code change? Did a field change type? Does a query still filter? Does a missing id still return 404 and `{}`? Does a create, update, or delete do what the docs say? These tests turn those questions into a run you can repeat.

The [guide](https://jsonplaceholder.typicode.com/#guide) says create, update, and delete return a success body and leave the stored resource unchanged. The write tests check both halves: the success response, and a follow-up read that still shows the original data.

The suite covers `/posts`, `/comments`, and `/users`: a list, a nested object, a filter, and a write that returns success. The expected shapes live in `tests/schemas.py`. The resource schemas set `additionalProperties` to false, so an unexpected field fails the test.

Posts (`tests/test_posts.py`):

- `GET /posts` and `GET /posts/1` return 200 and match the post schema (`userId`, `id`, `title`, `body`).
- Ids are integers. `title` and `body` are non-empty strings.
- `GET /posts?userId=1` returns only that user's posts, and a shorter list than `GET /posts`. The test fails if any returned post has another `userId`, or if the filter returns the full list.
- `GET /posts?userId=999999` returns 200 and `[]`. A filter with no match is an empty list. A missing id is a different answer: `GET /posts/0` and `GET /posts/999999` return 404 and `{}`.
- `GET /posts/1/comments` returns only comments whose `postId` is 1.
- `POST /posts` returns 201, echoes the sent fields, and includes an integer `id`. The following `GET` of that id returns 404 and `{}`.
- `PUT /posts/1` returns 200 and echoes the sent JSON. The following `GET /posts/1` still has the original title.
- `DELETE /posts/1` returns 200 and `{}`. The following `GET /posts/1` still returns the post.

Comments (`tests/test_comments.py`):

- `GET /comments` and `GET /comments/1` return 200 and match the comment schema (`postId`, `id`, `name`, `email`, `body`).
- Ids are integers. `name`, `email`, and `body` are non-empty strings, and `email` contains `@`.
- `GET /comments?postId=1` returns only that post's comments, and a shorter list than `GET /comments`.
- `GET /comments/0` and `GET /comments/999999` return 404 and `{}`.
- `POST /comments` returns 201 and the sent fields. The following `GET` of the new id returns 404 and `{}`.

Users (`tests/test_users.py`):

- `GET /users` and `GET /users/1` return 200 and match the user schema, including nested `address`, `address.geo`, and `company`.
- `address.geo.lat` and `address.geo.lng` are strings. The tests check both with `isinstance(..., str)`.
- `GET /users/1` is the sample user whose `username` is `Bret`.
- `GET /users?username=Bret` returns that one user.
- `GET /users/0` and `GET /users/999999` return 404 and `{}`.

Client errors (`tests/test_client.py`) use a fake transport, so they stay off the network. A timeout raises `ApiError` and records the timeout that was passed in. A connection error raises `ApiError`. An HTTP 200 whose body is not JSON raises `ApiError` with `status_code` 200. A base URL with a trailing slash and a path with a leading slash still join to one URL. `ApiError` is for those transport and body failures. A 404 from JSONPlaceholder stays an `ApiResponse` with a status code, because the server answered.

Each contract test is generated twice in `tests/conftest.py`. The `mock` copy always runs. The `live` copy is marked `live` and skipped until you pass `--live` or set `API_TEST_LIVE`.

The mock reads `tests/fixtures/`: posts 1, 2, and 11; comments 1, 2, and 6; users 1 (`Bret`) and 2 (`Antonette`). On 12 November 2026, live `GET /posts`, `GET /comments`, and `GET /users` returned 100, 500, and 10 records. The assertions check behavior that holds for the sample and for that live catalog, such as every post from `?userId=1` having `userId` 1.

## Test run

Commands below were run from the repository root on 12 November 2026 with Python 3.12.3, after `python -m pip install -e ".[dev]"`. That install resolved pytest 9.2.0, requests 2.34.2, responses 0.26.3, jsonschema 4.26.0, and ruff 0.17.4. `python -m ruff check .` printed `All checks passed!`.

`python -m pytest` uses the fixtures. The block is an excerpt of that run: the session header, the per-file lines, and the final summary. Pytest printed 21 `SKIPPED` lines between the per-file lines and the summary. Each one says live checks are off. `rootdir` is the checkout path on the machine that produced the log.

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /agent/repos/api-test-suite
configfile: pyproject.toml
testpaths: tests
collected 52 items

tests/test_client.py ....                                                [  7%]
tests/test_comments.py .s.s.s.s..ss.s                                    [ 34%]
tests/test_posts.py .s.s.s.s.s.s..ss.s.s.s                               [ 76%]
tests/test_users.py .s.s.s.s..ss                                         [100%]

======================== 28 passed, 24 skipped in 0.10s ========================
```

`python -m pytest --live` called `https://jsonplaceholder.typicode.com`. This is the full log:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /agent/repos/api-test-suite
configfile: pyproject.toml
testpaths: tests
collected 52 items

tests/test_client.py ....                                                [  7%]
tests/test_comments.py ..............                                    [ 34%]
tests/test_posts.py ......................                               [ 76%]
tests/test_users.py ............                                         [100%]

============================== 52 passed in 1.89s ==============================
```

On the same day, `API_TEST_LIVE=1 python -m pytest -m live` and `python -m pytest --live -m live` each finished with 24 passed and 28 deselected. `python -m pytest -m "not live"` finished with 28 passed and 24 deselected.

## Setup

Python 3.11 or newer. `pyproject.toml` sets `requires-python` to `>=3.11`. GitHub Actions runs the mocked suite on 3.11 and 3.12. The log above is Python 3.12.3.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Debian and Ubuntu, `python3 -m venv` needs the distro package that provides `ensurepip`. If creation fails with `ensurepip is not available`, install the package named in the error and run the three commands again. On Ubuntu with Python 3.12 that package is `python3.12-venv`:

```bash
sudo apt install python3.12-venv
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Single quotes around `'.[dev]'` keep PowerShell from treating `[dev]` as a wildcard.

If script activation is blocked by execution policy, call the venv Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest
```

## Run the tests

From the activated environment:

```bash
python -m ruff check .
python -m pytest
python -m pytest --live
```

`python -m pytest` answers from `tests/fixtures/`. CI uses this mode. The four tests in `tests/test_client.py` always use a fake transport.

Live copies stay skipped until you opt in. `tests/conftest.py` treats `--live` and `API_TEST_LIVE` the same way. The variable accepts `1`, `true`, and `yes` after trimming and lowercasing.

- `python -m pytest --live` runs the mock copy and the live copy.
- `API_TEST_LIVE=1 python -m pytest` does the same.
- `python -m pytest --live -m live` runs only the live copy.
- `API_TEST_LIVE=1 python -m pytest -m live` runs only the live copy.
- `python -m pytest -m "not live"` runs only the mock copy, including the client error tests.

The `live` marker is registered in `pyproject.toml`. Add `-v` to any pytest command to print each test name.

PowerShell:

```powershell
python -m pytest --live
$env:API_TEST_LIVE = "1"
python -m pytest -m live
```

## Tech stack

- Python 3.11 or newer. CI runs 3.11 and 3.12. The log in this file is Python 3.12.3.
- [requests](https://requests.readthedocs.io/) `>=2.31` for HTTP. This log used 2.34.2.
- [pytest](https://docs.pytest.org/) `>=8.0` for the suite. This log used 9.2.0.
- [responses](https://github.com/getsentry/responses) `>=0.25` to mock HTTP in the default run. This log used 0.26.3.
- [jsonschema](https://python-jsonschema.readthedocs.io/) `>=4.21` for response shape. This log used 4.26.0.
- [ruff](https://docs.astral.sh/ruff/) `>=0.6` for lint. This log used 0.17.4.
- GitHub Actions, in `.github/workflows/ci.yml`.

Version floors live in `pyproject.toml`. The versions next to "this log" are what pip installed on 12 November 2026 for the run above.

## Continuous integration

[![CI](https://github.com/dkupratis-debug/api-test-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/dkupratis-debug/api-test-suite/actions/workflows/ci.yml)

The workflow is named CI. On every push and pull request it runs `python -m ruff check .` and `python -m pytest` on Python 3.11 and 3.12. The job "Live JSONPlaceholder tests" runs when someone starts the workflow by hand (Actions tab, CI, Run workflow) and then runs `python -m pytest --live -m live` on Python 3.12.

## Project layout

```text
apitests/
  __init__.py
  client.py                 # base URL, timeout, GET/POST/PUT/DELETE, ApiError
tests/
  conftest.py               # mock and live copies, --live, API_TEST_LIVE
  mock_api.py               # fixture-backed stand-in for JSONPlaceholder
  schemas.py                # expected JSON shapes and field types
  fixtures/
    posts.json              # posts 1, 2, and 11
    comments.json           # comments 1, 2, and 6
    users.json              # users 1 (Bret) and 2 (Antonette)
  test_posts.py
  test_comments.py
  test_users.py
  test_client.py            # timeout, connection error, non-JSON body, URL joining
.github/workflows/ci.yml
pyproject.toml
LICENSE
```

## License

MIT. Copyright (c) 2026 David Kupratis.
