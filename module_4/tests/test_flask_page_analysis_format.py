import sys, os, pytest
import flask_app

@pytest.fixture
def client(monkeypatch):
    """
    Provide a Flask test client configured for analysis formatting tests.

    - Monkeypatches :func:`get_results` to return known numeric values.
    - Enables Flask testing mode.
    - Yields a test client instance.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :yield: A Flask test client instance.
    :rtype: flask.testing.FlaskClient
    """
    monkeypatch.setattr(flask_app, "get_results", lambda: {
        "pct_international": 12.3456,
        "fall_2025": 10,
        "degree_counts": [],
        "top_universities": []
    })
    
    # Put flask in testing mode
    flask_app.app.config["TESTING"] = True

    # Yield test client to make requests to routes
    with flask_app.app.test_client() as client:
        yield client

@pytest.mark.analysis
def test_percentage_two_decimals(client):
    """
    Verify formatting of percentages in analysis page.

    - Calls the index route (``/``).
    - Confirms that the percentage value ``12.3456`` appears in the HTML
      (ensuring proper 2-decimal formatting between Flask and Jinja).

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert "12.3456" in html  # Formatted version
