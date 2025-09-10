import os
import io
import json
import re
from datetime import datetime
from typing import Any, List, Dict, Tuple
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()   # Looks for .env file in the directory and pulls credentials from it

# Pulls in the credential data from the .env file
DSN = (
    f"host={os.getenv('PGHOST')} port={os.getenv('PGPORT')} "
    f"dbname={os.getenv('PGDATABASE')} user={os.getenv('PGUSER')} "
    f"password={os.getenv('PGPASSWORD')}"
)

# Create filepath to the target data
INPUT_JSON = os.path.join(os.path.dirname(__file__), "llm_extend_applicant_data.json")

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
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]

# Set up SQL for columns
insert_cols = ", ".join(COLUMNS)                                                # Create comma separated list of column names from above
placeholders = ", ".join(["%s"] * len(COLUMNS))                                 # Create comma separated list of %s data placeholders from above
update_cols = ", ".join(f"{c}=EXCLUDED.{c}" for c in COLUMNS if c != "p_id")    # Creates a default list of .EXCLUDED entries if there is an error in inserting the data

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
  gre DOUBLE PRECISION,
  gre_v DOUBLE PRECISION,
  gre_aw DOUBLE PRECISION,
  degree DOUBLE PRECISION,
  llm_generated_program TEXT,
  llm_generated_university TEXT
);
"""

# Update and insert (upsert) 
UPSERT_SQL = f"""
INSERT INTO applicants ({insert_cols})  # Inserts a new row in the applicants table
VALUES ({placeholders})                 # Value placeholders for each corresponding column
ON CONFLICT (p_id) DO UPDATE SET        # If there is a conflict, update the columns
  {update_cols};
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
    raw = raw.strip()   # Strip leading and ending whitespace

    if not raw:         # If raw data is empty, returns an empty list
        return []
    try:                # Try to load entire json file as an object
        obj = json.loads(raw)
        return obj["items"] if isinstance(obj, dict) and "items" in obj else obj
    except json.JSONDecodeError:    # If reading json file as an object fails, use this as a fail safe to read data line by line
        items=[]
        for line in raw.splitlines():
            s=line.strip()          # Strip white space
            if s:                   # If the cleaned string is non-empty, append it to the list
                items.append(json.loads(s))
        return items

def to_date(s):

    if not s: return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d","%m/%d/%Y","%d-%b-%Y","%b %d, %Y"):
        try: return datetime.strptime(s, fmt).date()
        except: pass
    return None

def to_float(x):

    if x in (None,"","NA","N/A","null"): return None
    m = re.search(r"-?\d+(\.\d+)?", str(x))
    return float(m.group(0)) if m else None

def extract_data(item, idx):

    return (
        int(item.get("p_id", idx)),                             # Primary key uses p_id unless it's missing, otherwise uses the loop index
        item.get("program"),                                    # Extract program data
        item.get("comments"),                                   # Extract comments/notes
        to_date(item.get("date_added")),                        # Extract date added and convert it to a date object to be consistent
        item.get("url"),                                        # Extract application url
        item.get("status"),                                     # Extract Application status
        item.get("term"),                                       # Extract semester/term data
        item.get("US/International"),                           # Extract US/international data
        to_float(item.get("gpa")),                              # Extract GPA and convert to float
        to_float(item.get("gre") or item.get("gre_q") or item.get("gre_quant")),                #writes nothing for now, need to push other data to db
        to_float(item.get("gre_v") or item.get("gre_verbal")),                                  #writes nothing for now, need to push other data to db
        to_float(item.get("gre_aw") or item.get("gre_awriting") or item.get("gre_aw_score")),   #writes nothing for now, need to push other data to db
        to_float(item.get("degree") or item.get("Degree")),                                     #writes nothing for now, need to push other data to db
        item.get("llm_generated_program") or item.get("llm-generated-program"),
        item.get("llm_generated_university") or item.get("llm-generated-university"),
    )

def main():
    
    items = read_items(INPUT_JSON)
    rows = []
    for i, item in enumerate(items):
        rows.append(extract_data(item, i + 1))

    with connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.executemany(UPSERT_SQL, rows)
        conn.commit()

    print(f"Pushed {len(rows)} rows into applicants.")

if __name__ == "__main__":
    main()