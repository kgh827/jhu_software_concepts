import subprocess
import types
import time
import src.flask_app as app
import pytest
pytestmark = pytest.mark.web

class InlineThread:
    """
    Fake replacement for :class:`threading.Thread`.

    Used to run scraper tasks synchronously during tests
    without creating background threads.
    """
    def __init__(self, target, args=(), kwargs=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}
    def start(self):
        self._target(*self._args, **self._kwargs)
    def join(self, *a, **k):
        return

@pytest.fixture
def client_base(monkeypatch):
    """
    Provide a baseline Flask test client with minimal monkeypatches.

    - Replaces :func:`get_results` and :func:`clean_data` with stubs.
    - Yields a Flask test client instance for route testing.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :yield: A Flask test client instance.
    :rtype: flask.testing.FlaskClient
    """
    monkeypatch.setattr(app, "get_results", lambda: {"total": 1})
    monkeypatch.setattr(app, "clean_data", lambda d: d)
    with app.app.test_client() as c:
        yield c

def test_pull_data_when_running(client_base, monkeypatch):
    """
    Verify ``/pull_data`` rejects requests if scraping is already running.

    - Sets the global scrape flag.
    - Ensures the response contains an error flash message.

    :param client_base: Flask test client.
    :type client_base: flask.testing.FlaskClient
    :param monkeypatch: Pytest fixture for patching.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    """
    app.scrape_running = True
    resp = client_base.get("/pull_data", follow_redirects=True)
    app.scrape_running = False
    assert resp.status_code == 200
    assert b"already running" in resp.data.lower()

def test_pull_data_llm_failure_exits_and_resets(monkeypatch, tmp_path, client_base):
    """
    Simulate LLM subprocess failure.

    - Forces :func:`subprocess.run` to raise an error.
    - Confirms :func:`load_data.main` is not called.
    - Ensures scrape flag resets to ``False``.

    :param monkeypatch: Pytest fixture for patching.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param tmp_path: Temporary file path for saving test data.
    :type tmp_path: pathlib.Path
    :param client_base: Flask test client.
    :type client_base: flask.testing.FlaskClient
    """
    # Monkeypatch in "InlineThread" in place of actual threading 
    monkeypatch.setattr(app.threading, "Thread", InlineThread)

    # Return one scraped record; save to a real temp file name
    monkeypatch.setattr(app, "scrape_data", lambda **k: [{"url":"http://x/1"}])
    out_file = tmp_path / "scraped.json"
    monkeypatch.setattr(app, "save_data", lambda data: str(out_file))
    monkeypatch.setattr(app, "clean_data", lambda d: d)

    # Force subprocess fail
    def fake_run(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])
    monkeypatch.setattr(app.subprocess, "run", fake_run)

    # Check that load_data.main should NOT be called
    called = {"n": 0}
    def fake_load_main(_):
        called["n"] += 1
    monkeypatch.setattr(app.load_data, "main", fake_load_main)

    # Hit endpoint and make sure load data is not called
    resp = client_base.get("/pull_data", follow_redirects=True)
    assert resp.status_code == 200
    assert called["n"] == 0             # LLM failed which causes early return, no DB load
    assert app.scrape_running is False  # Reset scrape_running to false

def test_pull_data_scrape_raises_still_resets(monkeypatch, client_base):
    """
    Verify scrape errors are handled gracefully.

    - Forces :func:`scrape_data` to raise an error.
    - Confirms the scrape flag resets to ``False``.

    :param monkeypatch: Pytest fixture for patching.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param client_base: Flask test client.
    :type client_base: flask.testing.FlaskClient
    """
    monkeypatch.setattr(app.threading, "Thread", InlineThread)

    # Fake function to simulate the scraper throwing an error
    def simulate_error(**k): 
        raise RuntimeError("simulate_error")
    monkeypatch.setattr(app, "scrape_data", simulate_error)

    # Confirm nothing else is reached and reset "scrape_running"
    resp = client_base.get("/pull_data", follow_redirects=True)
    assert resp.status_code == 200
    assert app.scrape_running is False

def test_pull_data_llm_success_calls_load(monkeypatch, tmp_path, client_base):
    """
    Simulate successful LLM processing.

    - Monkeypatches :func:`subprocess.run` to emulate success.
    - Confirms :func:`load_data.main` is called with the JSONL output.
    - Ensures scrape flag resets to ``False``.

    :param monkeypatch: Pytest fixture for patching.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param tmp_path: Temporary file path for saving test data.
    :type tmp_path: pathlib.Path
    :param client_base: Flask test client.
    :type client_base: flask.testing.FlaskClient
    """
    monkeypatch.setattr(app.threading, "Thread", InlineThread)
    monkeypatch.setattr(app, "scrape_data", lambda **k: [{"url":"http://x/1"}])
    out_file = tmp_path / "scraped.json"
    monkeypatch.setattr(app, "save_data", lambda data: str(out_file))
    monkeypatch.setattr(app, "clean_data", lambda d: d)

    # Simulate successfull subprocess attempt
    def ok_run(*a, **k): return subprocess.CompletedProcess(a, 0)
    monkeypatch.setattr(app.subprocess, "run", ok_run)

    # Define and simulate a fake replacement for load_data()
    called = {"args": None}
    def fake_load_main(p):
        called["args"] = p
    monkeypatch.setattr(app.load_data, "main", fake_load_main)

    # Press the pull data button
    resp = client_base.get("/pull_data", follow_redirects=True)
    assert resp.status_code == 200

    # Ensure our fake load_data.main was called
    assert called["args"] and called["args"].endswith(".jsonl")
    assert app.scrape_running is False

def test_update_analysis_during_scrape(monkeypatch, client_base):
    """
    Verify ``/update_analysis`` refuses while scraping is in progress.

    - Sets the global scrape flag to ``True``.
    - Ensures the response contains an error flash message.

    :param monkeypatch: Pytest fixture for patching.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param client_base: Flask test client.
    :type client_base: flask.testing.FlaskClient
    """
    app.scrape_running = True
    resp = client_base.get("/update_analysis", follow_redirects=True)
    app.scrape_running = False
    assert resp.status_code == 200
    assert b"cannot update analysis" in resp.data.lower()
