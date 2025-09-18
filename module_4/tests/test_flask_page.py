import pytest
import subprocess
import src.flask_app as flask_app
import src.flask_app as app

"""
This file tests flask app responses when things go as intended
"""

@pytest.fixture
def client(monkeypatch):
    """
    Provide a Flask test client with monkeypatched dependencies.

    This fixture:
      - Replaces :func:`get_results` with dummy values.
      - Stubs :func:`scrape_data`, :func:`clean_data`, :func:`save_data`,
        and :func:`load_data` with no-op implementations.
      - Yields a Flask test client for route testing.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :yield: A Flask test client instance.
    :rtype: flask.testing.FlaskClient
    """
    monkeypatch.setattr(app, "get_results", lambda: {"total": 1, "fall_2025": 1})
    monkeypatch.setattr(app, "scrape_data", lambda *a, **k: [])
    monkeypatch.setattr(app, "clean_data", lambda d: d)
    monkeypatch.setattr(app, "save_data", lambda d: "fake.json")
    monkeypatch.setattr(app, "load_data", lambda f: None)

    # Setting up fake flask http request for testing
    with app.app.test_client() as client:
        yield client

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
    