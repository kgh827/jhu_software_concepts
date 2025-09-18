import os
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load database credentials from .env file
load_dotenv()

# DSN (Data Source Name) string constructed from environment variables
DSN = (
    f"host={os.getenv('PGHOST')} port={os.getenv('PGPORT')} "
    f"dbname={os.getenv('PGDATABASE')} user={os.getenv('PGUSER')} "
    f"password={os.getenv('PGPASSWORD')}"
)

def sql_query(sql, *params):
    # Run a query against the PostgreSQL database and return rows as dicts.
    with connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)                    # Execute query
            return cur.fetchall()

def pct(x):
    return f"{x:.2f}%"  # Convert value to percent

def get_results():
    # Run the same set of queries as `main()`, but instead of printing, return results in a dictionary to use on the flask site
    
    results = {}

    results["total"] = sql_query("SELECT COUNT(*) AS total FROM applicants;")[0]["total"]

    # Question 1: Query to determine the number of applicants for the fall 2025 semester
    q1 = sql_query("SELECT COUNT(*) AS n FROM applicants WHERE term ILIKE %s;", "%Fall 2025%")
    results["fall_2025"] = q1[0]["n"]

    # Question 2: Query to determine number of applicants who were international students (NOT american and NOT other) to 2 decimals
    q2 = sql_query("""
        SELECT ROUND(
            100.0 * COUNT(*) FILTER (WHERE us_or_international ILIKE %s)
            / NULLIF(COUNT(*), 0), 2
        ) AS pct_international
        FROM applicants;
    """, "%internat%")
    results["pct_international"] = q2[0]["pct_international"]

    # Question 3: Query to find the average of GPA, GRE_q, GRE_V, GRE AW scores
    q3 = sql_query("""
        SELECT
          ROUND(AVG(gpa)::numeric, 3)    AS avg_gpa_4,
          ROUND(AVG(gre_q)::numeric, 3)  AS avg_gre_q,
          ROUND(AVG(gre_v)::numeric, 3)  AS avg_gre_v,
          ROUND(AVG(gre_aw)::numeric, 3) AS avg_gre_aw
        FROM applicants;
    """)
    results["avg_gpa_4"]  = q3[0]["avg_gpa_4"]
    results["avg_gre_q"]  = q3[0]["avg_gre_q"]
    results["avg_gre_v"]  = q3[0]["avg_gre_v"]
    results["avg_gre_aw"] = q3[0]["avg_gre_aw"]

    # Question 4: Query to find the average GPA of students for the fall 2025 semester
    q4 = sql_query("""
        SELECT ROUND(AVG(gpa)::numeric, 3) AS avg_gpa_us_fall25
        FROM applicants
        WHERE term ILIKE %s
          AND us_or_international ILIKE %s;
    """, "%Fall 2025%", "%American%")
    results["avg_gpa_us_fall25"] = q4[0]["avg_gpa_us_fall25"]

    # Question 5: Query to determine percentage (to 2 decimal places) of students from fall 2025 semester were accepted
    q5 = sql_query(
        "SELECT ROUND(100.0 * AVG(CASE WHEN status ILIKE %s THEN 1 ELSE 0 END), 2) "
        "AS pct_accept_fall25 FROM applicants WHERE term ILIKE %s;",
        "%accept%", "%Fall 2025%"
    )
    results["pct_accept_fall25"] = q5[0]["pct_accept_fall25"]

    # Question 6: Query to determine average gpa of applicants who were accepted in fall 2025    
    q6 = sql_query(
        "SELECT ROUND(AVG(gpa)::numeric, 3) AS avg_gpa_accept_fall25 "
        "FROM applicants WHERE term ILIKE %s AND status ILIKE %s;",
        "%Fall 2025%", "%accept%"
    )
    results["avg_gpa_accept_fall25"] = q6[0]["avg_gpa_accept_fall25"]

    # Question 7: Query to determine number of applicants for jhu computer science
    q7 = sql_query(
        "SELECT COUNT(*) AS n FROM applicants "
        "WHERE llm_generated_university ILIKE %s AND llm_generated_program ILIKE %s "
        "AND degree ILIKE %s;",
        "%johns hopkins%", "%computer science%", "%master%"
    )
    results["jhu_masters_cs"] = q7[0]["n"]

    # Question 8: Query to determine acceptances at georgetown university for phd in computer science
    q8 = sql_query(
        "SELECT COUNT(*) AS n FROM applicants "
        "WHERE term ILIKE %s AND status ILIKE %s "
        "AND llm_generated_university ILIKE %s "
        "AND llm_generated_program ILIKE %s AND degree ILIKE %s;",
        "%2025%", "%accept%", "%georgetown%", "%computer science%", "%phd%"
    )
    results["georgetown_cs_phd"] = q8[0]["n"]

    # Custom question 9: Most common applicant degree type
    q9 = sql_query("""
        SELECT degree, COUNT(*) AS n
        FROM applicants
        GROUP BY degree
        ORDER BY n DESC;
    """)
    results["degree_counts"] = [dict(r) for r in q9]

    # Custom question 10: Top 10 most common universities and the number of applicants
    q10 = sql_query("""
        SELECT llm_generated_university, COUNT(*) AS n
        FROM applicants
        WHERE llm_generated_university IS NOT NULL
        GROUP BY llm_generated_university
        ORDER BY n DESC
        LIMIT 10;
    """)
    results["top_universities"] = [dict(r) for r in q10]

    return results

def url_exists_in_db(url):
    # This function checks if the URL for a given student is already in the database
    # Returns a list with 1 columnif a given url exists, returns empty list otherwise
    result = sql_query("SELECT 1 FROM applicants WHERE url = %s LIMIT 1;", url) 
    return len(result) > 0

def main():
    # Determine total number of applicant data rows in the db
    total = sql_query("SELECT COUNT(*) AS total FROM applicants;")[0]["total"]  # Executing a query to determine the number of rows in the db
    print("Total number of rows in applicants database:", total)

    # Question 1: Query to determine the number of applicants for the fall 2025 semester
    q1 = sql_query("SELECT COUNT(*) AS n FROM applicants WHERE term ILIKE %s;", "%Fall 2025%")
    print("1) Fall 2025 entries:", q1[0]["n"])

    # Question 2: Query to determine number of applicants who were international students (NOT american and NOT other) to 2 decimals
    q2 = sql_query("""
        SELECT ROUND(
            100.0 * COUNT(*) FILTER (WHERE us_or_international ILIKE %s)
            / NULLIF(COUNT(*), 0), 2
        ) AS pct_international
        FROM applicants;
    """, "%internat%")
    print("2) International entries (%):", pct(q2[0]["pct_international"]))

    # Question 3: Query to find the average of GPA, GRE_q, GRE_V, GRE AW scores
    q3 = sql_query("""
        SELECT
          ROUND(AVG(gpa)::numeric, 3)    AS avg_gpa_4,
          ROUND(AVG(gre_q)::numeric, 3)  AS avg_gre_q,
          ROUND(AVG(gre_v)::numeric, 3)  AS avg_gre_v,
          ROUND(AVG(gre_aw)::numeric, 3) AS avg_gre_aw
        FROM applicants;
    """)
    print("3) Averages (GPA(on 4.0 scale) / GRE Q / GRE V / GRE AW):",
          q3[0]["avg_gpa_4"], q3[0]["avg_gre_q"], q3[0]["avg_gre_v"], q3[0]["avg_gre_aw"])

    # Question 4: Query to find the average GPA of students for the fall 2025 semester
    q4 = sql_query("""
        SELECT ROUND(AVG(gpa)::numeric, 3) AS avg_gpa_us_fall25
        FROM applicants
        WHERE term ILIKE %s
          AND us_or_international ILIKE %s;
    """, "%Fall 2025%", "%American%")
    print("4) Avg GPA (4.0-scale) of American students, Fall 2025:", q4[0]["avg_gpa_us_fall25"])

    # Question 5: Query to determine percentage (to 2 decimal places) of students from fall 2025 semester were accepted
    q5 = sql_query("""SELECT ROUND(100.0 * AVG(CASE 
                   WHEN status ILIKE %s THEN 1 ELSE 0 END), 2) AS pct_accept_fall25 
                   FROM applicants WHERE term ILIKE %s; """, "%accept%", "%Fall 2025%")
    print("5) Acceptance rate for Fall 2025:", pct(q5[0]["pct_accept_fall25"]))

    # Question 6: Query to determine average gpa of applicants who were accepted in fall 2025
    q6 = sql_query("""SELECT ROUND(AVG(gpa)::numeric, 3) AS avg_gpa_accept_fall25 FROM applicants 
                   WHERE term ILIKE %s AND status ILIKE %s;""", "%Fall 2025%", "%accept%")
    print("6) Avg GPA (4.0-scale) of Fall 2025 Acceptances:", q6[0]["avg_gpa_accept_fall25"])

    # Question 7: Query to determine number of applicants for jhu computer science
    q7 = sql_query("""SELECT COUNT(*) AS n FROM applicants 
                   WHERE llm_generated_university ILIKE %s AND llm_generated_program ILIKE %s 
                   AND degree ILIKE %s;""", "%johns hopkins%", "%computer science%", "%master%")
    print("7) JHU Masters in CS entries:", q7[0]["n"])

    # Question 8: Query to determine acceptances at georgetown university for phd in computer science
    q8 = sql_query("""
        SELECT COUNT(*) AS n
        FROM applicants
        WHERE term ILIKE %s
        AND status ILIKE %s
        AND llm_generated_university ILIKE %s
        AND llm_generated_program ILIKE %s
        AND degree ILIKE %s;
    """, "%2025%", "%accept%", "%georgetown%", "%computer science%", "%phd%")
    print("8) 2025 CS PhD acceptances to Georgetown:", q8[0]["n"])

    # Custom question 9: Most common applicant degree type
    q9 = sql_query("""
        SELECT degree, COUNT(*) AS n
        FROM applicants
        GROUP BY degree
        ORDER BY n DESC;
    """)
    print("9) Applicants by degree:")
    for row in q9:
        print(f"   {row['degree']}: {row['n']}")

    # Custom question 10: Top 10 most common universities and the number of applicants
    q10 = sql_query("""
        SELECT llm_generated_university, COUNT(*) AS n
        FROM applicants
        WHERE llm_generated_university IS NOT NULL
        GROUP BY llm_generated_university
        ORDER BY n DESC
        LIMIT 10;
    """)
    print("10) Top 10 universities by applicant count:")
    for row in q10:
        print(f"   {row['llm_generated_university']}: {row['n']}")

if __name__ == "__main__":  # pragma: no cover
    main()
