import pytest
import subprocess
import src.flask_app as flask_app
import src.flask_app as app
import requests
import urllib3
import socket
import subprocess
import src.flask_app as app


@pytest.fixture
def client(monkeypatch):
    # Stub subprocesses called by /pull_data and friends

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))

    # Stub urllib3 used by scraping paths (prevents DNS lookups)
    # Mirrors the pattern used in scraper tests
    class _DummyPool:
        def request(self, method, url, *args, **kwargs):
            class _Resp:
                # urllib3 expects a .data attribute (bytes)
                data = b"<html><body><table></table></body></html>"
            return _Resp()
    monkeypatch.setattr(urllib3, "PoolManager", lambda: _DummyPool())

    # Stub requests in case any route uses it directly
    class _RequestsResp:
        status_code = 200
        text = "{}"
        def json(self): return {}
    monkeypatch.setattr(requests.Session, "request",
                        lambda self, method, url, *a, **k: _RequestsResp())

    # (Optional but belt-and-suspenders) neuter raw DNS to avoid stray getaddrinfo calls
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))])


    monkeypatch.setattr(app, "get_results", lambda: {"total": 1, "fall_2025": 1})
    monkeypatch.setattr(app, "scrape_data", lambda *a, **k: [])
    monkeypatch.setattr(app, "clean_data", lambda d: d)
    monkeypatch.setattr(app, "save_data", lambda d: "fake.json")
    monkeypatch.setattr(app.load_data, "main", lambda *a, **k: None)

    with app.app.test_client() as client:
        yield client

@pytest.mark.web
def test_index_route(client):
    """
    Verify the index (``/``) route.

    - Confirms the response status code is 200.
    - Ensures the rendered page contains the word ``Analysis``.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Analysis" in resp.data

@pytest.mark.web
def test_pull_data_route(client):
    """
    Verify the ``/pull_data`` route.

    - Triggers scraping and LLM pipeline.
    - Confirms redirect and success flash message.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    resp = client.get("/pull_data", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Scraping + LLM processing started" in resp.data

@pytest.mark.web
def test_update_analysis_route(client):
    """
    Verify the ``/update_analysis`` route.

    - Confirms it refreshes analysis successfully.
    - Ensures HTML title ``Grad School Cafe Data Analysis`` is present.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    resp = client.get("/update_analysis", follow_redirects=True)
    assert resp.status_code == 200
    assert b"<title>Grad School Cafe Data Analysis</title>" in resp.data

@pytest.mark.web
def test_mock_llm(monkeypatch):
    """
    Test behavior when the LLM subprocess runs successfully.

    - Monkeypatches :func:`subprocess.run` to emulate success.
    - Confirms ``/pull_data`` redirects back to the home page.

    :param monkeypatch: Pytest fixture for patching subprocess behavior.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    """
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(subprocess, "run", fake_run)

    # Perform a "pull_data"
    client = flask_app.app.test_client()
    resp = client.get("/pull_data")

    # Redirect back to home page after
    assert resp.status_code == 302  
    