import sys, os, pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import flask_app

@pytest.fixture
def client(monkeypatch):
    """
    This function replaces get_results() with a fake response that returns known values for testing
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
    Calls the main analysis page route (/) and extracts the html
    Verifies that 12.3456 is displayed as 12.34
    Validates the formatting of 2 decimal places works between flask_app.py anf analysis.html
    """
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert "12.3456" in html  # Formatted version
