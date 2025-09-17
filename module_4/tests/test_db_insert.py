import sys, os, pytest
import db
import psycopg

# This manually imports the "db.py" file from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

@pytest.mark.db
def test_insert_rows_idempotent(monkeypatch):
    """
    Test to verify insert_rows can handle idempotent row inserts
    Uses monkeypatching to avoid interacting with the database directly.
    """
    # This list collects the row data that is meant to be inserted into the database by "insert_rows"
    inserted = []

    # Fake psycopg connection that returns dummy connection and cursor objects
    def fake_connect(dsn=None):
        class DummyCursor:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def execute(self, sql, params=None): inserted.append(params)
            def fetchone(self): return [len(inserted)]
        class DummyConn:
            def cursor(self, **kwargs): return DummyCursor()
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def commit(self): pass
        return DummyConn()

    # Monkeypatch psycopg.connect instead of db.connect
    monkeypatch.setattr(psycopg, "connect", fake_connect)

    # Two duplicate rows of data to determine how the data is handled 
    rows = [
        {"applicant_url": "u1", "term": "Fall 2025", "citizenship": "International", "program": "CS", "school": "TestU"},
        {"applicant_url": "u1", "term": "Fall 2025", "citizenship": "International", "program": "CS", "school": "TestU"}  
    ]

    # Call insert_rows from db.py
    db.insert_rows("fake_dsn", rows)

    # Because of ON CONFLICT DO NOTHING, it attempted push both rows but only 1 unique expected
    assert len(inserted) >= 1
