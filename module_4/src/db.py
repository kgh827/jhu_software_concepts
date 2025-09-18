import psycopg
from contextlib import contextmanager

@contextmanager
def get_conn(dsn):
    """
    Open and yield a PostgreSQL database connection.

    This context manager establishes a connection to the PostgreSQL
    database using the provided DSN (Data Source Name). The connection
    is automatically cleaned up when the context ends.

    :param dsn: Database connection string used to establish the connection.
    :type dsn: str
    :yield: A live PostgreSQL connection object.
    :rtype: psycopg.Connection
    """
    with psycopg.connect(dsn) as conn:
        yield conn

def ensure_schema(dsn):
    """
    Ensure that the ``applicants`` table exists in the database.

    This function connects to the database and creates the table
    ``applicants`` if it does not already exist. The table schema
    includes fields for applicant details such as URL, term,
    citizenship, program, school, GPA, and GRE.

    :param dsn: Database connection string used to establish the connection.
    :type dsn: str
    :return: None
    :rtype: NoneType
    """
    
    with get_conn(dsn) as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id SERIAL PRIMARY KEY,
            applicant_url TEXT UNIQUE NOT NULL,
            term TEXT NOT NULL,
            citizenship TEXT NOT NULL,
            program TEXT NOT NULL,
            school TEXT NOT NULL,
            gpa NUMERIC NULL,
            gre NUMERIC NULL
        );
        """)
        conn.commit()

def insert_rows(dsn, rows):
    """
    Insert multiple applicant records into the ``applicants`` table.

    Each row is expected to be a dictionary with the following keys:
    ``applicant_url``, ``term``, ``citizenship``, ``program``, ``school``,
    and optionally ``gpa`` and ``gre``. If a record with the same
    ``applicant_url`` already exists, the conflict is ignored.

    :param dsn: Database connection string used to establish the connection.
    :type dsn: str
    :param rows: A list of applicant dictionaries to insert.
    :type rows: list[dict[str, str | float | None]]
    :return: None
    :rtype: NoneType
    """
    with get_conn(dsn) as conn, conn.cursor() as cur:
        for r in rows:
            cur.execute("""
                INSERT INTO applicants (applicant_url, term, citizenship, program, school, gpa, gre)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (applicant_url) DO NOTHING
            """, (r["applicant_url"], r["term"], r["citizenship"], r["program"], r["school"], r.get("gpa"), r.get("gre")))
        conn.commit()

def count_rows(dsn):
    """
    Count the number of records in the ``applicants`` table.

    Executes a ``SELECT COUNT(*)`` query to determine the total number
    of rows currently stored in the table.

    :param dsn: Database connection string used to establish the connection.
    :type dsn: str
    :return: The total number of rows in the table.
    :rtype: int
    """
    with get_conn(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        return cur.fetchone()[0]
