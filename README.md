# API Test Suite

Practice project by David Kupratis for support engineering, QA, tooling, and test automation.

This repo checks the contract of [JSONPlaceholder](https://jsonplaceholder.typicode.com), a free public REST API built for practice. When a client and an API stop agreeing, the useful questions are specific. Did the status code change? Did a field change type? Does `?userId=1` still filter? Does a missing id still return 404? Do create, update, and delete do what the docs say? These tests turn those questions into something you can re-run locally and in CI.

JSONPlaceholder accepts `POST`, `PUT`, and `DELETE`, then forgets the write. That behavior is documented in the [guide](https://jsonplaceholder.typicode.com/guide/). The write tests check both parts: the success response, and a follow-up read that still shows the original data.

## Tech stack

- Python 3.11 and 3.12
- [requests](https://requests.readthedocs.io/) for HTTP
- [pytest](https://docs.pytest.org/) for the suite
- [responses](https://github.com/getsentry/responses) to mock HTTP in the default run
- [jsonschema](https://python-jsonschema.readthedocs.io/) for response shape
- [ruff](https://docs.astral.sh/ruff/) for lint
- GitHub Actions for CI

Library floors live in `pyproject.toml`. The logs below used the versions pip installed on 12 November 2026 (pytest 9.2.0, and the others resolved that day).

## Project layout

```text
apitests/
  client.py            # base URL, timeout, GET/POST/PUT/DELETE, clear errors
tests/
  conftest.py          # mock vs live switch, --live flag, live marker
  mock_api.py          # local stand-in for JSONPlaceholder
  schemas.py           # expected JSON shapes and field types
  fixtures/            # small responses recorded from the real API
  test_posts.py
  test_comments.py
  test_users.py
  test_client.py       # timeouts and bad bodies, no network
.github/workflows/ci.yml
pyproject.toml
```

The fixture files are a recorded sample: posts 1, 2, and 11, comments 1, 2, and 6, and users 1 and 2. The live API currently has 100 posts, 500 comments, and 10 users. The tests check behavior that holds for both the sample and the live catalog, such as every filtered post having `userId` 1.

## Run the tests

Python 3.11 or newer.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest
python -m pytest --live
```

Live tests only, using the environment variable:

```bash
API_TEST_LIVE=1 python -m pytest -m live
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m ruff check .
python -m pytest
python -m pytest --live
$env:API_TEST_LIVE = "1"
python -m pytest -m live
```

Single quotes around `'.[dev]'` keep PowerShell from treating `[dev]` as a wildcard.

If script activation is blocked by execution policy, call the venv Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest
```

Add `-v` to any pytest command to print each test name.

## Mocked mode and live mode

`python -m pytest` answers from local fixtures. `tests/conftest.py` starts the `responses` mock, and `tests/mock_api.py` reads `tests/fixtures/`. CI uses this mode.

Each contract test runs twice. The `mock` copy always runs. The `live` copy is marked `live` and skipped until you opt in:

- `python -m pytest --live` runs the mock copy and the live copy
- `API_TEST_LIVE=1` does the same thing as `--live` (values `1`, `true`, and `yes` count)
- `python -m pytest --live -m live` runs only the live copy
- `python -m pytest -m "not live"` runs only the mock copy, including the client error tests

The `live` marker is registered in `pyproject.toml`. `conftest.py` attaches it to the live copy of each contract test, so each behavior is written once.

The four tests in `tests/test_client.py` always use a fake transport. They simulate a timeout, a connection error, a non-JSON body, and URL joining.

GitHub Actions (`.github/workflows/ci.yml`) runs `ruff check` and `python -m pytest` on Python 3.11 and 3.12 for every push and pull request. The "Live JSONPlaceholder tests" job runs only when someone starts the workflow by hand (Actions tab, CI, Run workflow). That job runs `python -m pytest --live -m live` on Python 3.12.

## What the tests check

Posts, comments, and users:

- list and get-by-id status codes
- JSON Schema shape, including nested user address and company
- field types in plain Python (`isinstance`), including geo coordinates stored as strings
- query filters: `GET /posts?userId=1`, `GET /comments?postId=1`, `GET /users?username=Bret`
- a filter that matches nothing is `200` and `[]`
- a missing id (`0` and `999999`) is `404` and `{}`
- `GET /posts/1/comments` returns only that post's comments
- `POST`, `PUT`, and `DELETE` on posts, and `POST` on comments, follow the documented fake-write behavior

`ApiError` is reserved for timeouts, connection failures, and bodies that are not JSON. A 404 is a normal response with a status code, because the server did answer.

## Local test run

Commands run from the project root on 12 November 2026. `python -m ruff check .` printed `All checks passed!` on Python 3.12.3 and on Python 3.11.18.

### Mocked (`python -m pytest`) on Python 3.12.3

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /workspace
configfile: pyproject.toml
testpaths: tests
collected 52 items

tests/test_client.py ....                                                [  7%]
tests/test_comments.py .s.s.s.s..ss.s                                    [ 34%]
tests/test_posts.py .s.s.s.s.s.s..ss.s.s.s                               [ 76%]
tests/test_users.py .s.s.s.s..ss                                         [100%]

=========================== short test summary info ============================
SKIPPED [1] tests/test_comments.py:17: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_comments.py:24: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_comments.py:36: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_comments.py:45: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [2] tests/test_comments.py:56: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_comments.py:64: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:28: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:35: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:46: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:55: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:66: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:73: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [2] tests/test_posts.py:81: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:89: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:104: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_posts.py:117: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_users.py:14: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_users.py:21: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_users.py:41: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [1] tests/test_users.py:50: live checks are off. Pass --live or set API_TEST_LIVE=1.
SKIPPED [2] tests/test_users.py:60: live checks are off. Pass --live or set API_TEST_LIVE=1.
======================== 28 passed, 24 skipped in 0.10s ========================
```

### Live (`python -m pytest --live`) on Python 3.12.3

This run called `https://jsonplaceholder.typicode.com`.

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /workspace
configfile: pyproject.toml
testpaths: tests
collected 52 items

tests/test_client.py ....                                                [  7%]
tests/test_comments.py ..............                                    [ 34%]
tests/test_posts.py ......................                               [ 76%]
tests/test_users.py ............                                         [100%]

============================== 52 passed in 2.99s ==============================
```

The same two commands on Python 3.11.18 finished with `28 passed, 24 skipped` (mocked) and `52 passed` (live). `API_TEST_LIVE=1 python -m pytest -m live` and `python -m pytest --live -m live` each ran the 24 live tests and passed.

## What I'd add next

- Playwright browser tests for a page that sits in front of an API. This repo checks HTTP only.
- Contract diffing that fails when a response gains a field, loses a field, or changes a field's type. `tests/schemas.py` is a hand-written version of that check.
- An HTML or JUnit report so a CI failure is easier to read than the raw log.
- Full recorded catalogs if exact sizes (100 posts, 10 users, 500 comments) should become part of the contract. The fixtures here are a small sample so the JSON stays readable.
- The same checks for `albums`, `todos`, and `photos`. The client and the mock router already work off the URL path, so those resources are more fixture files and test modules.

## License

MIT. Copyright (c) 2026 David Kupratis.
