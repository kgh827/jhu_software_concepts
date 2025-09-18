import sys, os, pytest
import flask_app

@pytest.fixture
def client(monkeypatch):
    """
    Provide a Flask test client with monkeypatched dependencies.

    - Uses an in-memory fake DB dictionary to track inserted rows.
    - Monkeypatches :func:`scrape_data`, :func:`clean_data`, :func:`load_data`,
      and :func:`get_results` to use the fake DB.
    - Enables Flask testing mode.
    - Yields a Flask test client.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :yield: Flask test client for making requests.
    :rtype: flask.testing.FlaskClient
    """
    # Set up fake DB
    fake_db = {"rows": []}

    # Monkeypatch scrape_data, clean_data, load_data, and get_results
    monkeypatch.setattr(flask_app, "scrape_data", lambda: [{"url": "fake"}])
    monkeypatch.setattr(flask_app, "clean_data", lambda rows: rows)
    monkeypatch.setattr(flask_app, "load_data", lambda cleaned: fake_db["rows"].extend(cleaned))
    monkeypatch.setattr(flask_app, "get_results", lambda: {
        "fall_2025": len(fake_db["rows"]),
        "pct_international": "0.00%",
        "degree_counts": [],
        "top_universities": []
    })

    # Put flask in testing mode
    flask_app.app.config["TESTING"] = True

    # Yield flask test client to simulate http requests
    with flask_app.app.test_client() as client:
        yield client

@pytest.mark.integration
def test_end_to_end_flow(client):
    """
    Full integration test covering app flow.

    - Simulates pressing ``pull_data`` and ``update_analysis`` buttons.
    - Loads the index route (``/``).
    - Confirms expected text is present in the rendered HTML.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    """
    # Simulate pressing "pull data" button
    resp = client.get("/pull_data")
    assert resp.status_code in (200, 302)

    # Simulate pressing "update analysis" button
    resp = client.get("/update_analysis")
    assert resp.status_code in (200, 302)

    # Load the analysis page (home / page)
    resp = client.get("/")
    html = resp.get_data(as_text=True)

    # Verify expected text is present
    assert "Applicant count" in html or "fall_2025" in html
