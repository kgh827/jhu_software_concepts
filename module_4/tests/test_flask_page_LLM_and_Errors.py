import subprocess
import types
import time
import src.flask_app as app
import pytest

class InlineThread:
    """
    This function fakes "threading.thread" in order to be able to 
    run the scraper without creating a background thread.
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
    This function simulates requests.
    It monkeypatches the minimum allowable default data for get_results and clean_data
    """
    monkeypatch.setattr(app, "get_results", lambda: {"total": 1})
    monkeypatch.setattr(app, "clean_data", lambda d: d)
    with app.app.test_client() as c:
        yield c

def test_pull_data_when_running(client_base, monkeypatch):
    """
    This simulates the pull data button being pressed while there is already a scrape running
    """
    app.scrape_running = True
    resp = client_base.get("/pull_data", follow_redirects=True)
    app.scrape_running = False
    assert resp.status_code == 200
    assert b"already running" in resp.data.lower()

def test_pull_data_llm_failure_exits_and_resets(monkeypatch, tmp_path, client_base):
    """
    Simulates LLM step failing (subprocess throws CalledProcessError) 
    Verifies load_data.main should NOT be called
    Verifies scrape_running reset back to false
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
    Test for when scrape_data raises an error, and the program handles the exception
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
    LLM path response if LLM succeeds
    Calls load_data.main with the produced jsonl path
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
    If scraping is running, update_analysis should refuse and flash a message
    """
    app.scrape_running = True
    resp = client_base.get("/update_analysis", follow_redirects=True)
    app.scrape_running = False
    assert resp.status_code == 200
    assert b"cannot update analysis" in resp.data.lower()
