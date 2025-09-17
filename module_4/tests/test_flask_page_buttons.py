import sys, os, pytest
import flask_app

@pytest.fixture
def client(monkeypatch):
    """
    This simulates a flask test client (i.e. a browser) 
    Monkeypatches ensure that the scrape_data, clean_data, load_data, and get_results functions dont actually run
    Fake placeholder data is included for each function.
    """
    monkeypatch.setattr(flask_app, "scrape_data", lambda: [{"url": "fake"}])
    monkeypatch.setattr(flask_app, "clean_data", lambda rows: rows)
    monkeypatch.setattr(flask_app, "load_data", lambda cleaned: None)
    monkeypatch.setattr(flask_app, "get_results", lambda: {"fall_2025": 1})

    # Put flask in testing mode
    flask_app.app.config["TESTING"] = True

    # Yield fake test client for fake response 
    with flask_app.app.test_client() as client:
        yield client

@pytest.mark.buttons
def test_pull_data_once(client):
    """
    This calls the pull data button once using the test client
    Monkeypatches in the client above makes sure no actual data processing is done
    This test indicates that the pull data button is working correctly
    """
    resp = client.get("/pull_data")
    assert resp.status_code in (200, 302)  # 200 means redirect was followed, 302 if not followed
