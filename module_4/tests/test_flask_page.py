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
    Monkeypatch all dependencies to allow tests to be predictable
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
    Test to check if the index page returns 200 and has the word "Analysis" in it
    """
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Analysis" in resp.data

def test_pull_data_route(client):
    """
    Perform a "pull_data" action and trigger the scraping and LLM portion of the code
    """
    resp = client.get("/pull_data", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Scraping + LLM processing started" in resp.data

def test_update_analysis_route(client):
    """
    Perform an "update_analysis" action and trigger the return of the analysis html.
    """
    resp = client.get("/update_analysis", follow_redirects=True)
    assert resp.status_code == 200
    assert b"<title>Grad School Cafe Data Analysis</title>" in resp.data

def test_mock_llm(monkeypatch):
    """
    This test emulates the LLM subprocess response to indicate a successful LLM run
    """
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(subprocess, "run", fake_run)

    # Perform a "pull_data"
    client = flask_app.app.test_client()
    resp = client.get("/pull_data")

    # Redirect back to home page after
    assert resp.status_code == 302  
    