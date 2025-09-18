import pytest
import src.query_data as qd

class DummyCursor:
    """
    Dummy database cursor for testing :mod:`query_data`.

    - Records executed SQL statements and parameters.
    - Returns canned results for specific queries
      (e.g., JHU Masters in CS, Georgetown PhD, applicant counts).
    - Used to simulate PostgreSQL behavior without a real DB.
    """

    def __init__(self):
        """
        Store history of sql commands (self.executed) and current results being fetched (self.results)
        """
        self.executed = []
        self.results = []

    def execute(self, sql, params=None):
        """
        This simulates running an sql query
        It accepts sql string and parameters
        Examines input text to determine what response to supply 
        """
        # Strip whitespace and make command lowercase
        s = (sql or "").strip().lower()
        self.executed.append((s, params))

        # Standardize params
        if params is None:
            params = ()
        param_lower = [("" if p is None else str(p)).lower() for p in params]

        # Combines everything into a string
        pl_join = " ".join(param_lower)

        # This section returns sql results based on the input patterns

        # JHU masters in computer science query
        if ("llm_generated_university ilike" in s and
            "llm_generated_program ilike" in s and
            "degree ilike" in s and
            "johns hopkins" in pl_join and
            "computer science" in pl_join and
            "master" in pl_join):
            self.results = [{"n": 7}]

        # Georgetown PhD in computer science query
        elif ("llm_generated_university ilike" in s and
              "llm_generated_program ilike" in s and
              "degree ilike" in s and
              "georgetown" in pl_join and
              "computer science" in pl_join and
              "phd" in pl_join):
            self.results = [{"n": 2}]

        # Applicant count query
        elif "select count(*) as total from applicants" in s:
            self.results = [{"total": 50}]
        
        # Fall 2025 query
        elif ("count(*) as n from applicants where term" in s and
              "llm_generated_university ilike" not in s and
              "llm_generated_program ilike" not in s and
              "degree ilike" not in s and
              ("fall 2025" in s or "fall 2025" in pl_join)):
            self.results = [{"n": 12}]
        
        # International vs American query
        elif "pct_international" in s:
            self.results = [{"pct_international": 33.3}]

        # GPA/GRE query
        elif "round(avg(gpa)::numeric, 3)    as avg_gpa_4" in s:
            self.results = [{
                "avg_gpa_4": 3.700,
                "avg_gre_q": 160.000,
                "avg_gre_v": 155.000,
                "avg_gre_aw": 4.500,
            }]

        # Average gpa for us students in fall 2025 query
        elif ("avg_gpa_us_fall25" in s and
              "where term ilike" in s and
              "and us_or_international ilike" in s):
            self.results = [{"avg_gpa_us_fall25": 3.600}]

        # Percent acceptances fall 2025 query
        elif "as pct_accept_fall25" in s and "where term ilike" in s:
            self.results = [{"pct_accept_fall25": 75.00}]

        # Average gpa accepted in fall 2025 query
        elif "as avg_gpa_accept_fall25" in s:
            self.results = [{"avg_gpa_accept_fall25": 3.800}]

        # Group applicants by degree query
        elif "from applicants" in s and "group by degree" in s:
            self.results = [
                {"degree": "MS", "n": 10},
                {"degree": "PhD", "n": 5},
            ]

        # LLM Cleaned university query
        elif "group by llm_generated_university" in s and "limit 10" in s:
            self.results = [
                {"llm_generated_university": "Test U", "n": 8},
                {"llm_generated_university": "Cool College", "n": 6},
            ]


        elif "select 1 from applicants where url" in s:
            # Default empty
            self.results = []

        # Any unmatched query returns as zero
        else:
            self.results = [{"n": 0}]

    def fetchall(self): 
        return self.results
    def fetchone(self): 
        return self.results[0]
    def __enter__(self): 
        return self
    def __exit__(self, *a): 
        return False


class DummyConn:
    """
    Dummy database connection for testing.

    - Returns :class:`DummyCursor` from :meth:`cursor`.
    - Implements context manager protocol.
    """
    def cursor(self, *a, **k): 
        return DummyCursor()
    def __enter__(self): 
        return self
    def __exit__(self, *a): 
        return False


@pytest.fixture(autouse=True)
def fake_psycopg(monkeypatch):
    """
    Automatically patch :func:`qd.connect` to return a dummy connection.

    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    """
    monkeypatch.setattr(qd, "connect", lambda dsn=None: DummyConn())


###################### Tests
@pytest.mark.analysis
def test_pct_formatting():
    """
    Verify :func:`qd.pct` percentage formatting.

    - Confirms correct rounding to two decimal places.
    - Handles zero input properly.
    """
    assert qd.pct(12.3456) == "12.35%"
    assert qd.pct(0) == "0.00%"

@pytest.mark.db
@pytest.mark.analysis
def test_get_results_all_keys_and_values():
    """
    Verify :func:`qd.get_results` runs all SQL queries.

    - Confirms expected keys are present in results.
    - Checks that dummy values are returned for counts and averages.
    - Validates list structures for degree counts and top universities.
    """
    results = qd.get_results()

    expected = {
        "total", "fall_2025", "pct_international",
        "avg_gpa_4", "avg_gre_q", "avg_gre_v", "avg_gre_aw",
        "avg_gpa_us_fall25", "pct_accept_fall25",
        "avg_gpa_accept_fall25", "jhu_masters_cs", "georgetown_cs_phd",
        "degree_counts", "top_universities",
    }
    missing = expected - set(results.keys())
    assert not missing, f"Missing keys: {missing}"

    # Check dummy values
    assert results["total"] == 50
    assert results["fall_2025"] == 12
    assert results["pct_international"] == 33.3
    assert results["avg_gpa_4"] == 3.700
    assert results["avg_gre_q"] == 160.000
    assert results["avg_gre_v"] == 155.000
    assert results["avg_gre_aw"] == 4.500
    assert results["avg_gpa_us_fall25"] == 3.600
    assert results["pct_accept_fall25"] == 75.00
    assert results["avg_gpa_accept_fall25"] == 3.800
    assert results["jhu_masters_cs"] == 7
    assert results["georgetown_cs_phd"] == 2

    # Check list structures
    deg = results["degree_counts"]
    top = results["top_universities"]
    assert isinstance(deg, list) and all(isinstance(x, dict) for x in deg)
    assert isinstance(top, list) and all(isinstance(x, dict) for x in top)
    assert {"degree": "MS", "n": 10} in deg
    assert {"llm_generated_university": "Test U", "n": 8} in top

@pytest.mark.db
def test_url_exists_in_db_true_false(monkeypatch):
    """
    url_exists_in_db() is dependent on sql_query()
    I used monkeypatch here instead of using dummycursor for true false responses
    """
    monkeypatch.setattr(qd, "sql_query", lambda *_a, **_k: [])
    assert qd.url_exists_in_db("http://none") is False

    monkeypatch.setattr(qd, "sql_query", lambda *_a, **_k: [{"dummy": 1}])
    assert qd.url_exists_in_db("http://exists") is True

@pytest.mark.db
@pytest.mark.analysis
def test_main_prints(capsys):
    """
    Verify :func:`qd.url_exists_in_db` true/false behavior.

    - Monkeypatches :func:`qd.sql_query` to return empty or non-empty lists.
    - Confirms output matches expectations.
    """
    qd.main()

    # Record stdout
    out = capsys.readouterr().out.lower()

    assert "total number of rows in applicants database:" in out
    assert "1) fall 2025 entries" in out
    assert "2) international entries (%)" in out
    assert "3) averages" in out
    assert "4) avg gpa (4.0-scale) of american students, fall 2025" in out
    assert "5) acceptance rate for fall 2025:" in out
    assert "6) avg gpa (4.0-scale) of fall 2025 acceptances:" in out
    assert "7) jhu masters in cs entries:" in out
    assert "8) 2025 cs phd acceptances to georgetown:" in out
    assert "9) applicants by degree:" in out
    assert "10) top 10 universities by applicant count:" in out

    # Check that some dummy data survived
    assert "50" in out                       # total
    assert "12" in out                       # fall_2025
    assert "75.0%" in out or "75.00%" in out # pct_accept_fall25 via pct()
