import os
import io
import json
import re
from datetime import datetime
from typing import Any, List, Dict, Tuple
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

BASE_DIR = os.path.dirname(__file__)    # Path to the current working directory of this script
LLM_JSON = os.path.join(BASE_DIR, "LLM_app_data_GRE_GPA.jsonl")     # Json of the new data set after being processed by the LLM (new data to be able to get GPA/GRE data)

# Set up the columns based on assignment description
COLUMNS: List[str] = [
    "p_id",
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre_q",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]

# Set up SQL for columns
insert_cols = ", ".join(COLUMNS)                                                # Create comma separated list of column names
placeholders = ", ".join(["%s"] * len(COLUMNS))                                 # Create placeholder %s characters for each corresponding column

# Setting up the SQL table commands
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applicants (
  p_id INTEGER PRIMARY KEY,
  program TEXT,
  comments TEXT,
  date_added DATE,
  url TEXT,
  status TEXT,
  term TEXT,
  us_or_international TEXT,
  gpa DOUBLE PRECISION,
  gre_q DOUBLE PRECISION,
  gre_v DOUBLE PRECISION,
  gre_aw DOUBLE PRECISION,
  degree TEXT,
  llm_generated_program TEXT,
  llm_generated_university TEXT
);
"""

# Insert sql data based on data outlined above
INSERT_SQL = f"""
INSERT INTO applicants ({insert_cols})
VALUES ({placeholders})
ON CONFLICT (p_id) DO NOTHING;
"""

def read_items(path):
    """
    Read and parse items from a JSON or JSON-lines file.

    Args:
        path (str): Path to the input file.

    Returns:
        items: List of items pulled from the file. If the file contains:
            - A JSON object with an "items" key returns value of data.
            - A plain JSON list returns the list.
            - JSON-lines (one JSON object per line) returns a list of parsed objects.
            - An empty file returns an empty list.
    """
    raw = io.open(path, "r", encoding="utf-8-sig").read()   # Open and read the json file contents as a string; encoding = utf-8-sig avoids byte order marks
    raw = raw.strip()                                       # Strip leading and ending whitespace

    if not raw:         # If raw data is empty, returns an empty list
        return []
    try:                # Try to load entire json file as an object
        obj = json.loads(raw)
        return obj["items"] if isinstance(obj, dict) and "items" in obj else obj
    except json.JSONDecodeError:    # If reading json file as an object fails, use this as a fail safe to read data line by line
        items = []
        for line in raw.splitlines():
            s = line.strip()        # Strip white space
            if s:                   # If the cleaned string is non-empty, append it to the list
                items.append(json.loads(s))
        return items

def to_date(s):
    if not s: 
        return None     # Return nothing if s does not exist
    s = str(s).strip()  # Strip whitepace

    # Standardize the month abbreviations to be consistent
    month_map = {
        "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
        "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
        "Sept": "September", "Oct": "October", "Nov": "November", "Dec": "December"
    }

    # Replace the abbreviations and eliminate any other "filler", meaning "-", "/" and ","
    split_date = s.replace("-", " ").replace("/", " ").replace(",", " ").split()

    new_date_parts = []                 # Empty list to store parts of the new date
    for part in split_date:
        part_Cap = part.capitalize()    # Capitalize the current part
        if part_Cap in month_map:       # If the month is found
            new_date_parts.append(month_map[part_Cap])  # Add to new_date_parts from "month_map" for standard month
        else:
            new_date_parts.append(part)                 # Otherwise add the year/day to new_date_parts 
    s = " ".join(new_date_parts)

    # Added a bunch of formats to try to catch any outliers
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%b-%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%B %d %Y",
        "%d %B",
        "%B %Y",
    ]

    # Checks each format above compared to the current date, if it matches any of them, it converts the match to a date object and returns it.
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except:     # Ignore error if it occurs
            pass
    return None     # return nothing if it fails

def to_float(x):
    if x in (None, "", "NA", "N/A", "null"):
        return None
    try:
        return float(x)
    except ValueError:
        return None

def clean_gpa(val):
    g = to_float(val)
    if g is None:
        return None
    return g if 0.0 <= g <= 4.0 else None

def clean_gre(val, kind):
    s = to_float(val)
    if s is None:
        return None                                 # if there if no score, ignore
    if kind == "aw":
        return s if 0.0 <= s <= 6.0 else None       # If the GRE analytical writing score is outside of the normal range, ignore
    return s if 130 <= s <= 170 else None           # If the GRE quantative/verbal score is outside of the normal range, ignore

def extract_data(item, idx):
    return (
        int(item.get("p_id", idx)),                     # Primary key uses p_id unless it's missing, otherwise uses the loop index
        item.get("program"),                            # Extract program data
        item.get("comments"),                           # Extract comments/notes
        to_date(item.get("date_added")),                # Extract date added and convert it to a date object to be consistent
        item.get("url") or item.get("applicant_URL"),   # Extract application url
        item.get("status"),                             # Extract Application status
        item.get("term"),                               # Extract semester/term data
        item.get("US/International") or item.get("us_or_international"),# Extract US/international data
        clean_gpa(item.get("gpa")),                     # Extract GPA
        clean_gre(item.get("gre_q"), "qv"),             # Extract gre_q and clean using clean_gre()
        clean_gre(item.get("gre_v"), "qv"),             # Extract gre_v and clean using clean_gre()
        clean_gre(item.get("gre_aw"), "aw"),            # Extract gre_aw and clean using clean_gre()
        item.get("degree") or item.get("Degree"),       # Ectract degree
        item.get("llm_generated_program") or item.get("llm-generated-program"),         # Extract llm program       
        item.get("llm_generated_university") or item.get("llm-generated-university"),   # Extract llm university
    )

def main():
    llm_items = read_items(LLM_JSON)

    rows = []
    for i, item in enumerate(llm_items):
        rows.append(extract_data(item, i + 1))

    with connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.executemany(INSERT_SQL, rows)
        conn.commit()

    print(f"Pushed {len(rows)} rows into applicants.")

if __name__ == "__main__":
    main()
