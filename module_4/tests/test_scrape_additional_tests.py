import pytest
import src.scrape as scrape
from bs4 import BeautifulSoup as RealSoup

class DummyHTTPResponse:
    """
    Dummy HTTP response for fake urllib3 calls.

    :param html: Fake HTML string.
    :type html: str
    """
    def __init__(self, html: str):
        self.data = html.encode("utf-8")

def make_pool(html_first: str, html_second: str = "<html><body><table></table></body></html>"):
    """
    Create dummy HTTP pool returning fake HTML.

    - First request returns ``html_first``.
    - Second request returns ``html_second``.

    :param html_first: HTML for first request.
    :type html_first: str
    :param html_second: HTML for subsequent requests.
    :type html_second: str
    :return: Dummy pool instance.
    :rtype: object
    """
    class DummyPool:
        def __init__(self):
            self.call_count = 0
        def request(self, method, url, *args, **kwargs):
            self.call_count += 1
            html = html_first if self.call_count == 1 else html_second
            return DummyHTTPResponse(html)
    return DummyPool()  # Returns an instance (not the class)

def patch_dependencies(monkeypatch, pool_instance):
    """
    Monkeypatch scraper dependencies for testing.

    - Replace PoolManager with dummy pool.
    - Use real BeautifulSoup parsing.
    - Force :func:`url_exists_in_db` to always return False.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param pool_instance: Dummy pool instance.
    :type pool_instance: object
    """
    # Make PoolManager() return our pool_instance
    monkeypatch.setattr(scrape.urllib3, "PoolManager", lambda: pool_instance)

    # Use real BeautifulSoup functionality
    class DummySoup:
        def __init__(self, *args, **kwargs):
            self.soup = RealSoup(args[0], "html.parser")
        def __getattr__(self, name):
            return getattr(self.soup, name)
    monkeypatch.setattr(scrape, "BeautifulSoup", DummySoup)

    # Force url_exists_in_db = false
    monkeypatch.setattr(scrape, "url_exists_in_db", lambda url: False)

@pytest.mark.integration
def test_decision_with_on_split(monkeypatch):
    """
    Verify decision/status split when "on" keyword is present.

    - Ensures applicant_status and decision_date fields are parsed.
    """
    # Fake HTML
    html = """
    <html><body><table>
      <tr>
        <td>Uni</td><td><span>CS</span><span>MS</span></td>
        <td>2025-01-01</td><td>Accepted on 2025-02-05</td>
        <td><a href="http://u" data-ext-page-id="1"></a></td>
      </tr>
      <!-- Second Row-1 to trigger append of the first -->
      <tr>
        <td>Uni2</td><td><span>Math</span><span>PhD</span></td>
        <td>2025-01-02</td><td>Rejected</td>
      </tr>
    </table></body></html>
    """
    pool = make_pool(html)
    patch_dependencies(monkeypatch, pool)
    r = scrape.scrape_data(max_applicants=1)

    # Check if applicant_status has been populated
    assert r and r[0]["applicant_status"] == "Accepted"

    # Check that decision_date has been populated.
    assert r[0]["decision_date"] == "2025-02-05"

@pytest.mark.integration
def test_row2_path_and_sleep(monkeypatch):
    """
    Verify row 2 handling without row 3.

    - Confirms GPA and GRE fields are extracted.
    - Ensures :func:`time.sleep` is called at least once per page.
    """
    # Fake HTML
    html = """
    <html><body><table>
      <tr>
        <td>Test U</td><td><span>EE</span><span>MS</span></td>
        <td>2025-03-01</td><td>Accepted</td>
        <td><a href="http://a" data-ext-page-id="1"></a></td>
      </tr>
      <tr class="tw-border-none">
        <td><span>Fall 2025</span><span>International</span><span>GPA 3.9</span><span>GRE 169</span></td>
      </tr>
      <!-- Next is a new Row-1 (no tw-border-none), so no Row-3 -->
      <tr>
        <td>Test U2</td><td><span>Math</span><span>PhD</span></td>
        <td>2025-03-02</td><td>Rejected</td>
      </tr>
    </table></body></html>
    """

    # Dictionary counter for number of sleep calls
    sleep_called = {"n": 0}

    # Using monkeypatching to call fake sleep function
    monkeypatch.setattr(scrape.time, "sleep", lambda x: sleep_called.__setitem__("n", sleep_called["n"] + 1))

    # Create dummy http connection to supply fake html
    pool = make_pool(html)
    patch_dependencies(monkeypatch, pool)
    r = scrape.scrape_data(max_applicants=2)

    # CHecks if data is valid, checks if time.sleep has happened
    assert r and r[0]["gpa"] == "3.9" and r[0]["gre_q"] == "169"
    assert sleep_called["n"] >= 1 

@pytest.mark.integration
def test_added_this_page_only_header(monkeypatch):
    """
    Verify scraper behavior when only table header is present.

    - Confirms scraper exits with no data when no rows are added.
    """
    html = """
    <html><body><table>
      <tr><th>Header</th></tr>
    </table></body></html>
    """
    pool = make_pool(html)
    patch_dependencies(monkeypatch, pool)
    r = scrape.scrape_data(max_applicants=5)
    # Checks for no data
    assert r == []

@pytest.mark.integration
def test_row3_path_and_reset(monkeypatch):
    """
    Verify row 3 path and reset logic.

    - Ensures notes are extracted.
    - Confirms row_check resets for next applicant.
    """
    html = """
    <html><body><table>
      <tr>
        <td>Test U</td><td><span>History</span><span>MA</span></td>
        <td>2025-05-01</td><td>Waitlisted</td>
        <td><a href="http://fakeurl3" data-ext-page-id="1">link</a></td>
      </tr>
      <tr class="tw-border-none">
        <td><span>Fall 2025</span><span>American</span><span>GPA 3.2</span></td>
      </tr>
      <tr class="tw-border-none">
        <td>Strong algebra background</td>
      </tr>
      <!-- Second Row-1 to trigger append without exceeding the limit -->
      <tr>
        <td>Next U</td><td><span>CS</span><span>MS</span></td>
        <td>2025-06-01</td><td>Accepted</td>
      </tr>
    </table></body></html>
    """
    pool = make_pool(html)
    patch_dependencies(monkeypatch, pool)
    r = scrape.scrape_data(max_applicants=2)
    assert r and "notes" in r[0] and r[0]["notes"].startswith("Strong")