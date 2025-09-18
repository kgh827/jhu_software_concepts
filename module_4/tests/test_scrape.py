import pytest
import src.scrape as scrape
from bs4 import BeautifulSoup as RealSoup


class DummyHTTPResponse:
    """
    Simulates fake HTTP response with HTML data
    """
    def __init__(self, html: str):
        self.data = html.encode("utf-8")

@pytest.mark.scraper
def test_scrape_decision_using_on(monkeypatch):
    """
    This html emulates the situation that is used for determining acceptance/waitlist/rejection
    date by using the word "on" (i.e. rejected ON ____, accepted ON _____)
    --> If ON is present --> Split the data into applicant status and date
    --> If ON is NOT present --> treat the cell as applicant_status without a date.
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

@pytest.mark.scraper
def test_scrape_row2_gre_q_aw(monkeypatch):
    """
    - This test simulates extraction of the GRE quantitative, analytical, and writing scores
      from fake HTML.
    - Row 2 of data is identified by "tw-border-none"
    - The scraper extracts data from <span><div> and sends them to:
    --> Spring 2026: Semester
    --> American: Student Location
    --> GRE 168: gre_q
    --> GRE AW 4.5: gre_aw
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

@pytest.mark.scraper
def test_scrape_limit(monkeypatch):
    """
    This tests whether the scraper "limit" can handle cutting off in the middle of a page
    The HTML given to the scraper are two one-row entries (no row 2 or 3)
    At the end it checks whether the length is 1.
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
    Monkeypatch urllib3 and beautifulsoup so the scraper can run without making external connections.
    - Page 1 contains the "offline" HTML
    - Page 2 contains an empty table prompting the scraper to stop

    This also simulates "url_exists_in_db()"
    - If stop_after_first = false --> url_exists_in_db() = false
    - If stop_after_first = true  --> returns false for first url, true for 2nd url (hits existing record)
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


@pytest.mark.scraper
def test_scrape_row1(monkeypatch):
    """
    This test checks that reading row 1 data and appending previous applicant once a "new" row 1 starts
    - Scraper has a dict active for current applicant (row_check = 1)
    - When scraper finds a "new" row 1, it appends the previous applicant data and starts a new applicant
    - Tested using two "row 1" rows consecutively, and should only write the first one (max_applicants = 1)
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


@pytest.mark.scraper
def test_scrape_row2(monkeypatch):
    """
    This test checks functionality of reading row 2 data (term, loction, gpa, gre)
    - Row 2 has "tw-border-none", so data gets pulled from nested spans/divs
    - This also contains a row 3 so that the "row_check=2" path is taken to append
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


@pytest.mark.scraper
def test_scrape_row3(monkeypatch):
    """
    This test checks functionality of reading row 3 data (notes)
    - Row 2 is the 2nd consecutive row containing "tw-border-none"
    - The scraper pulls data_entries[0] to as notes if they are present
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


@pytest.mark.scraper
def test_scrape_existing_url_stop(monkeypatch):
    """
    This test verifies that the scraper halts after finding a duplicate record if url_exists_in_db = true.
    - This only works after at least one applicant has been appended.
    - First applicant url returns false
    - Second applicant url returns true
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
