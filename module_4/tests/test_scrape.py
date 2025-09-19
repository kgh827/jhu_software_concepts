import pytest
import src.scrape as scrape
from bs4 import BeautifulSoup as RealSoup


class DummyHTTPResponse:
    """
    Dummy HTTP response for simulating urllib3 requests.

    :param html: Fake HTML string to embed as response body.
    :type html: str
    """
    def __init__(self, html: str):
        self.data = html.encode("utf-8")

@pytest.mark.integration
def test_scrape_decision_using_on(monkeypatch):
    """
    Verify decision parsing when status contains "on".

    - If "on" is present, split into status and decision date.
    - If not, treat cell as status only.
    """
    html = """
    <table>
      <tr>
        <td>Uni</td><td><span>CS</span><span>MS</span></td>
        <td>2025-01-01</td><td>Waitlisted (no date)</td>
      </tr>
      <tr>
        <td>Next Uni</td><td><span>Math</span><span>PhD</span></td>
        <td>2025-01-02</td><td>Rejected</td>
      </tr>
    </table>
    """

    # Monkeypatch with dummy html for beautifulsoup offline use
    patch_with_html(monkeypatch, f"<html><body>{html}</body></html>")

    # Scraper runs for 1 record
    r = scrape.scrape_data(max_applicants=1)

    # Tests that without "on" the cell should contain applicant_status only
    assert r[0]["applicant_status"] == "Waitlisted (no date)"  # no ' on ' split

@pytest.mark.integration
def test_scrape_row2_gre_q_aw(monkeypatch):
    """
    Verify GRE extraction in row 2.

    - Confirms ``gre_q`` and ``gre_aw`` fields are parsed.
    - Checks that semester and student location are extracted.
    """
    html = """
    <table>
      <tr>
        <td>U</td><td><span>CS</span><span>MS</span></td>
        <td>2025-01-01</td><td>Accepted</td>
        <td><a href="http://x" data-ext-page-id="1"></a></td>
      </tr>
      <tr class="tw-border-none">
        <td><span>Spring 2026</span><span>American</span>
            <span>GRE 168</span><span>GRE AW 4.5</span></td>
      </tr>
      <tr>
        <td>Sentinel</td><td><span>A</span><span>B</span></td>
        <td>2025-01-02</td><td>Accepted</td>
      </tr>
    </table>
    """
    patch_with_html(monkeypatch, f"<html><body>{html}</body></html>")
    r = scrape.scrape_data(max_applicants=1)

    # Check that each field aligns
    assert r[0]["gre_q"] == "168"
    assert r[0]["gre_aw"] == "4.5"
    assert r[0]["semester"].startswith("Spring")
    assert "American" in r[0]["student_location"]

@pytest.mark.integration
def test_scrape_limit(monkeypatch):
    """
    Verify scraper stops at max_applicants limit.

    - Uses two dummy rows.
    - Confirms only one is returned.
    """
    html = """
    <table>
      <tr><td>U1</td><td><span>CS</span><span>MS</span></td><td>2025</td><td>A</td></tr>
      <tr><td>U2</td><td><span>EE</span><span>PhD</span></td><td>2025</td><td>A</td></tr>
    </table>
    """
    patch_with_html(monkeypatch, f"<html><body>{html}</body></html>")
    r = scrape.scrape_data(max_applicants=1)
    assert len(r) == 1

def patch_with_html(monkeypatch, html: str, stop_after_first: bool = False):
    """
    Monkeypatch urllib3 and BeautifulSoup for offline scraping.

    - First page returns supplied HTML.
    - Subsequent pages return empty table.
    - Allows simulating :func:`url_exists_in_db`.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param html: Fake HTML content.
    :type html: str
    :param stop_after_first: Whether to simulate duplicate URL after first record.
    :type stop_after_first: bool
    """

    # Creates a fake urllib3.poolmanager.request
    class DummyPool:
        def __init__(self):
            self.call_count = 0

        
        def request(self, method, url, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                # First page returns the HTML 
                return DummyHTTPResponse(html)
            
            # Pages after the first page return empty page
            return DummyHTTPResponse("<html><body><table></table></body></html>")

    # Prevent use of real HTTP
    monkeypatch.setattr(scrape.urllib3, "PoolManager", lambda: DummyPool())

    # Use real beautifulsoup interaction
    class DummySoup:
        def __init__(self, *args, **kwargs):
            self.soup = RealSoup(args[0], "html.parser")
        def __getattr__(self, name):
            return getattr(self.soup, name)

    monkeypatch.setattr(scrape, "BeautifulSoup", DummySoup)

    # Fake DB check:
    #- If stop_after_first = false --> url_exists_in_db() = false
    #- If stop_after_first = true  --> returns false for first url, true for 2nd url (hits existing record)
    calls = {"n": 0}
    def fake_exists(url):
        calls["n"] += 1
        if stop_after_first:
            return calls["n"] > 1
        return False

    # Prevent http
    monkeypatch.setattr(scrape, "url_exists_in_db", fake_exists)


@pytest.mark.integration
def test_scrape_row1(monkeypatch):
    """
    Verify row 1 handling.

    - Confirms new row appends previous applicant record.
    - Uses two consecutive row-1 entries.
    """
    fake_html = """
    <html><body><table>
      <!-- First applicant (will be appended when the next Row-1 starts) -->
      <tr>
        <td>Test University</td>
        <td><span>CompSci</span><span>MS</span></td>
        <td>2025-09-01</td>
        <td>Accepted</td>
      </tr>
      <!-- Second Row-1 starts a new applicant; scraper appends the previous one here -->
      <tr>
        <td>Test2 U</td>
        <td><span>Math</span><span>PhD</span></td>
        <td>2025-09-02</td>
        <td>Rejected</td>
      </tr>
    </table></body></html>
    """
    patch_with_html(monkeypatch, fake_html)
    results = scrape.scrape_data(max_applicants=1)

    # Check that the entry only contains row 1
    assert results and results[0]["university"] == "Test University"


@pytest.mark.integration
def test_scrape_row2(monkeypatch):
    """
    Verify row 2 handling.

    - Confirms GPA, GRE, and other fields are extracted.
    - Ensures appending occurs when row 3 follows.
    """
    fake_html = """
    <html><body><table>
      <tr>
        <td>Test U</td><td><span>Math</span><span>PhD</span></td>
        <td>2025-01-01</td><td>Rejected</td>
        <td><a href="http://fakeurl2" data-ext-page-id="1">link</a></td>
      </tr>
      <tr class="tw-border-none">
        <td><span>Fall 2025</span><span>International</span>
            <span>GPA 3.8</span><span>GRE V 160</span></td>
      </tr>
      <!-- Dummy Row-3 ensures append from row_check==2 path -->
      <tr class="tw-border-none"><td></td></tr>
    </table></body></html>
    """
    patch_with_html(monkeypatch, fake_html)
    results = scrape.scrape_data(max_applicants=1)
    # Checks that the data is written correctly
    assert results and "gpa" in results[0]


@pytest.mark.integration
def test_scrape_row3(monkeypatch):
    """
    Verify row 3 handling.

    - Confirms notes field is extracted.
    - Triggered by second "tw-border-none" row.
    """
    fake_html = """
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
        <td>I love programming</td>
      </tr>
    </table></body></html>
    """
    patch_with_html(monkeypatch, fake_html)
    results = scrape.scrape_data(max_applicants=1)

    # Checks that the notes are present
    assert results and "notes" in results[0]


@pytest.mark.integration
def test_scrape_existing_url_stop(monkeypatch):
    """
    Verify scraper halts on existing URL.

    - First URL is unique.
    - Second URL triggers :func:`url_exists_in_db` and stops scraping.
    """
    fake_html = """
    <html><body><table>
      <!-- First applicant -->
      <tr>
        <td>Stop U</td><td><span>CS</span><span>PhD</span></td>
        <td>2025-08-01</td><td>Accepted</td>
        <td><a href="http://fakeurl4a" data-ext-page-id="1">link</a></td>
      </tr>
      <!-- Second applicant row-1: triggers append of the first, then hits True on url_exists_in_db -->
      <tr>
        <td>Next U</td><td><span>EE</span><span>MS</span></td>
        <td>2025-08-02</td><td>Accepted</td>
        <td><a href="http://fakeurl4b" data-ext-page-id="1">link</a></td>
      </tr>
    </table></body></html>
    """
    patch_with_html(monkeypatch, fake_html, stop_after_first=True)
    # Set max_applicants to 5 so that if the early stop fails, it stops at 2 records
    results = scrape.scrape_data(max_applicants=5)
    # CHeck to make sure there is only one result (because we faked a second url result)
    assert len(results) == 1

@pytest.mark.integration
def test_scrape_page_is_alias(monkeypatch):
    """
    Verify :func:`scrape.scrape_page` delegates to :func:`scrape.scrape_data`.

    - Confirms alias call executes underlying scraper.
    """
    import src.scrape as s
    called = {}

    def fake_scrape_data(arg, latest_date_in_db=None):
        called["ran"] = True
        return []

    monkeypatch.setattr(s, "scrape_data", fake_scrape_data)
    s.scrape_page("http://example.com")
    assert called.get("ran") is True