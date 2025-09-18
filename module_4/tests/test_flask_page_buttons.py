import sys, os, pytest
import flask_app

@pytest.fixture
def client(monkeypatch):
    """
    Provide a Flask test client for button route testing.

    - Monkeypatches scraping, cleaning, loading, and results functions
      to prevent side effects.
    - Enables Flask testing mode.
    - Yields a test client instance.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :yield: A Flask test client instance.
    :rtype: flask.testing.FlaskClient
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
    Verify the pull data button behavior.

    - Calls ``/pull_data`` once with a test client.
    - Confirms response status is 200 (redirect followed) or 302 (redirect pending).

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    resp = client.get("/pull_data")
    assert resp.status_code in (200, 302)  # 200 means redirect was followed, 302 if not followed
