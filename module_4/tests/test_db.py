import pytest
import src.db as db


# Shared dummy connection object that records activity
class DummyCursor:
    def __init__(self):
        self.executed = []
        self.results = [(0,)]  # default return for SELECT COUNT(*)

    def execute(self, sql, params=None):
        # Track executed SQL
        self.executed.append((sql.strip(), params))
        if sql.strip().startswith("SELECT COUNT(*)"):
            self.results = [(42,)]

    def fetchone(self):
        return self.results[0]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class DummyConn:
    def __init__(self):
        self.cursor_obj = DummyCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# Global instance so both insert_rows and test see the same object
dummy_conn = DummyConn()


@pytest.fixture(autouse=True)
def fake_psycopg(monkeypatch):
    """Monkeypatch psycopg.connect to always return the same DummyConn."""
    monkeypatch.setattr(db.psycopg, "connect", lambda dsn: dummy_conn)
    # Reset state before each test
    dummy_conn.cursor_obj.executed.clear()
    dummy_conn.committed = False


@pytest.mark.db
def test_ensure_schema_runs():
    """ensure_schema should run CREATE TABLE without error."""
    db.ensure_schema("fake_dsn")
    # Verify a CREATE TABLE statement was executed
    assert any("CREATE TABLE" in sql for sql, _ in dummy_conn.cursor_obj.executed)


@pytest.mark.db
def test_insert_rows_executes_insert():
    """insert_rows should execute INSERT statements and commit."""
    rows = [
        {
            "applicant_url": "http://fake1",
            "term": "Fall 2025",
            "citizenship": "International",
            "program": "CS",
            "school": "Foo U",
            "gpa": 3.8,
            "gre": 320,
        }
    ]
    db.insert_rows("fake_dsn", rows)

    executed_sqls = [sql for sql, _ in dummy_conn.cursor_obj.executed]
    assert any("INSERT INTO applicants" in sql for sql in executed_sqls)
    assert dummy_conn.committed


@pytest.mark.db
def test_count_rows_returns_value():
    """count_rows should return the fake SELECT COUNT(*) value."""
    count = db.count_rows("fake_dsn")
    assert count == 42
