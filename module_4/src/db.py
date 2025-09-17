import psycopg
from contextlib import contextmanager

@contextmanager
def get_conn(dsn):
    """ 
    This function opens a PostgreSQL connection and cleans up
    dsn --> database connection string
    """
    with psycopg.connect(dsn) as conn:
        yield conn

def ensure_schema(dsn):
    """ 
    This function connects to the database and adds the table if it does not exist
    If the table does not exist, it is created here
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
    This function connects to the database and writes applicant data
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
    This function is used to count the current number of rows in the applicant table.
    """
    with get_conn(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicants;")
        return cur.fetchone()[0]
