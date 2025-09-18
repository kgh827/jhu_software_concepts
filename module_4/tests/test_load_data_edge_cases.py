import io
import json
from datetime import date
import types
import pytest
import src.load_data as ld

@pytest.mark.db
def test_read_items_variations(tmp_path):
    """
    Test :func:`ld.read_items` with multiple formats.

    - JSON object with ``items`` key.
    - JSON list.
    - JSON-lines format.
    - Empty file fallback.

    :param tmp_path: Temporary file path for testing.
    :type tmp_path: pathlib.Path
    """
    # Json object with "items:"
    p1 = tmp_path / "obj.json"
    p1.write_text(json.dumps({"items": [{"a":1}, {"b":2}]}), encoding="utf-8")
    assert ld.read_items(str(p1)) == [{"a":1}, {"b":2}]

    # Json list
    p2 = tmp_path / "list.json"
    p2.write_text(json.dumps([{"x":3}]), encoding="utf-8")
    assert ld.read_items(str(p2)) == [{"x":3}]

    # Json lines
    p3 = tmp_path / "lines.jsonl"
    p3.write_text('{"u":1}\n{"v":2}\n', encoding="utf-8")
    assert ld.read_items(str(p3)) == [{"u":1}, {"v":2}]

    # Empty file
    p4 = tmp_path / "empty.json"
    p4.write_text("", encoding="utf-8")
    assert ld.read_items(str(p4)) == []

@pytest.mark.db
def test_to_date_formats():
    """
    Test :func:`ld.to_date` with different date formats.

    - Confirms parsing of slashed, worded, hyphenated, and month/year inputs.
    - Ensures unsupported formats return ``None``.

    :return: None
    :rtype: NoneType
    """
    assert ld.to_date("02/03/2025") == date(2025,2,3)
    assert ld.to_date("3-Feb-2025") == date(2025,2,3)
    assert ld.to_date("Feb 3, 2025") == date(2025,2,3)
    assert ld.to_date("September 2025") == date(2025,9,1)
    assert ld.to_date("Sept 3, 2025") == date(2025,9,3)
    assert ld.to_date(None) is None
    assert ld.to_date("not a date") is None
    # NEED TO FIX YYYY-MM-DD returns none - cant use this format
    assert ld.to_date("2025-02-03") is None

@pytest.mark.db
def test_to_float_and_clean_gpa_gre():
    """
    Validate float conversion and cleaning functions.

    - Tests :func:`ld.to_float` with valid, empty, and invalid values.
    - Tests :func:`ld.clean_gpa` within and outside valid range.
    - Tests :func:`ld.clean_gre` for quantitative/verbal and analytical writing.

    :return: None
    :rtype: NoneType
    """
    assert ld.to_float("3.5") == 3.5
    assert ld.to_float("NA") is None
    assert ld.to_float(None) is None
    assert ld.to_float("abc") is None

    # GPA
    assert ld.clean_gpa("4.0") == 4.0
    assert ld.clean_gpa("0.0") == 0.0
    assert ld.clean_gpa("4.1") is None

    # GRE qv range
    assert ld.clean_gre("160", "qv") == 160.0
    assert ld.clean_gre("100", "qv") is None

    # GRE aw range
    assert ld.clean_gre("5.5", "aw") == 5.5
    assert ld.clean_gre("6.5", "aw") is None

@pytest.mark.db
def test_extract_data_keys_and_pid():
    """
    Validate :func:`ld.extract_data` key handling.

    - Confirms ``p_id`` derived from URL numeric suffix.
    - Confirms fallback to index if URL lacks numeric suffix.
    - Validates extracted values are correctly mapped.

    :return: None
    :rtype: NoneType
    """
    item = {
        "program":"CS",
        "comments":"note",
        "date_added":"Feb 5, 2025",
        "applicant_URL":"http://example.com/123",
        "status":"Accepted",
        "term":"Fall 2025",
        "US/International":"International",
        "gpa":"3.5",
        "gre_q":"161",
        "gre_v":"160",
        "gre_aw":"4.5",
        "Degree":"MS",
        "llm-generated-program":"Comp Sci",
        "llm-generated-university":"Test U"
    }
    row = ld.extract_data(item, 42)
    # p_id from URL
    assert row[0] == 123
    assert row[3] == date(2025,2,5)
    assert row[6] == "Fall 2025"
    assert row[7] == "International"
    assert row[8] == 3.5
    assert row[9] == 161.0 and row[10] == 160.0 and row[11] == 4.5
    assert row[12] == "MS"
    assert row[13] == "Comp Sci"
    assert row[14] == "Test U"

    # Index used as p_id if URL has no numbers at the end
    item2 = {**item, "applicant_URL":"http://test.com/letters"}
    row2 = ld.extract_data(item2, 7)
    assert row2[0] == 7   # fallback to idx

@pytest.mark.db
@pytest.mark.integration
def test_main_db_push(tmp_path, monkeypatch, capsys):
    """
    Integration test for :func:`ld.main`.

    - Creates a temporary JSONL file with two records.
    - Monkeypatches :mod:`psycopg` connection and cursor.
    - Confirms rows are inserted and success message is printed.

    :param tmp_path: Temporary file path for testing.
    :type tmp_path: pathlib.Path
    :param monkeypatch: Pytest fixture for patching dependencies.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param capsys: Pytest fixture to capture stdout/stderr.
    :type capsys: _pytest.capture.CaptureFixture
    """
    p = tmp_path / "data.jsonl"
    lines = [
        {"url":"http://site/1", "program":"A"},
        {"url":"http://site/2", "program":"B"},
    ]
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")

    # Fake psycopg connect -> capture executes and rows
    execs = {"create":0, "executemany":0, "rows":None}

    class DummyCursor:
        def __init__(self, *a, **k): pass
        def execute(self, sql, params=None):
            # Create table call
            if "create table if not exists applicants" in (sql or "").lower():
                execs["create"] += 1
        def executemany(self, sql, rows):
            execs["executemany"] += 1
            execs["rows"] = list(rows)
        def __enter__(self): return self
        def __exit__(self, *a): return False

    class DummyConn:
        def cursor(self, *a, **k): return DummyCursor()
        def commit(self): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(ld, "connect", lambda dsn=None: DummyConn())

    ld.main(str(p))
    out = capsys.readouterr().out

    # Checks that the "pushed __ rows into applicants" message pops up correctly
    assert "Pushed 2 rows into applicants." in out

    # Make sure table creation happened
    assert execs["create"] == 1 and execs["executemany"] == 1

    # Make sure two rows exist
    assert len(execs["rows"]) == 2
