import os
import io
import json
from datetime import datetime
from typing import Any, List, Dict, Tuple
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv
from datetime import datetime, date
import re

# Load database credentials from .env file
load_dotenv()

# DSN (Data Source Name) string constructed from environment variables
DSN = (
    f"host={os.getenv('PGHOST')} port={os.getenv('PGPORT')} "
    f"dbname={os.getenv('PGDATABASE')} user={os.getenv('PGUSER')} "
    f"password={os.getenv('PGPASSWORD')}"
)

BASE_DIR = os.path.dirname(__file__)                                # Path to the current working directory of this script
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

    Attempts multiple strategies depending on file structure:
    
    - If the file is empty, returns an empty list.
    - If the file contains a JSON object with an ``items`` key,
      returns the value of that key.
    - If the file contains a JSON array, returns the array.
    - If the file is JSON-lines formatted (one JSON object per line),
      returns a list of parsed objects.

    :param path: Path to the input file.
    :type path: str
    :return: Parsed list of items.
    :rtype: list[dict]
    """
    raw = io.open(path, "r", encoding="utf-8-sig").read()   # Open and read the json file contents as a string; encoding = utf-8-sig avoids byte order marks
    raw = raw.strip()                                       # Strip leading and ending whitespace

    if not raw:                     # If raw data is empty, returns an empty list
        return []
    try:                            # Try to load entire json file as an object
        obj = json.loads(raw)
        return obj["items"] if isinstance(obj, dict) and "items" in obj else obj
    except json.JSONDecodeError:    # If reading json file as an object fails, use this as a fail safe to read data line by line
        items = []
        for line in raw.splitlines():
            s = line.strip()        # Strip white space
            if s:                   # If the cleaned string is non-empty, append it to the list
                items.append(json.loads(s))
        return items


def to_date(s: str | None) -> date | None:
    """
    Convert a string into a :class:`datetime.date` if possible.

    Supported formats include:
    
    - ``MM/DD/YYYY`` or ``M/D/YYYY``
    - ``MM/DD/YY`` or ``M/D/YY``
    - Worded formats: e.g. ``Feb 3 2025``, ``3 February 2025``
    - Hyphenated formats: e.g. ``03-Feb-25``
    - Month + Year only: e.g. ``September 2025`` (defaults to day = 1)
    - Ordinals: e.g. ``3rd`` → ``3``
    - Abbreviated months: e.g. ``Sept.`` → ``Sep``

    Returns ``None`` if parsing fails.

    :param s: Input string containing a date.
    :type s: str | None
    :return: Parsed date object or ``None``.
    :rtype: datetime.date | None
    """
    if not s or not s.strip():
        return None

    raw = s.strip()

    # 1) Slash formats first (keep slashes intact)
    if "/" in raw:
        for fmt in ("%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass  # try next

    # 2) Normalize for worded & hyphenated formats
    t = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", raw, flags=re.I)   # 3rd -> 3
    t = re.sub(r"\bSept\.?\b", "Sep", t, flags=re.I)              # Sept./Sept -> Sep
    t = re.sub(r"\b(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.\b", r"\1", t, flags=re.I)
    t = t.replace("-", " ")                                       # 3-Feb-2025 -> 3 Feb 2025
    t = re.sub(r"[.,]", " ", t)                                   # strip commas/periods
    t = re.sub(r"\s+", " ", t).strip()

    # 3) Day-present worded formats (4- and 2-digit years)
    for fmt in ("%b %d %Y", "%B %d %Y", "%d %b %Y", "%d %B %Y",
                "%b %d %y", "%B %d %y", "%d %b %y", "%d %B %y"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue

    # 4) Month + Year only -> default to day=1 (e.g., "September 2025")
    for fmt in ("%B %Y", "%b %Y"):
        try:
            return datetime.strptime(t, fmt).date()  # becomes YYYY-MM-01
        except ValueError:
            continue

    return None

def to_float(x):
    """
    Convert a value into a float if valid.

    - Returns ``None`` for missing values such as ``None``, ``""``, ``"NA"``,
      ``"N/A"``, or ``"null"``.
    - Returns ``float(x)`` if conversion succeeds.
    - Returns ``None`` if conversion fails.

    :param x: Input value to convert.
    :type x: str | int | float | None
    :return: Converted float or ``None``.
    :rtype: float | None
    """
    if x in (None, "", "NA", "N/A", "null"):        # If the value is equal to common empty data sequences
        return None                                 # Return "None"
    try:
        return float(x)                             # Otherwise return the float of the input value                        
    except ValueError:                              # Except Value Error to keep script going
        return None                                 # Return "None" if reach this point

def clean_gpa(val): 
    """
    Validate and normalize GPA values.

    - Returns ``None`` if the input is invalid.
    - Returns the GPA as a float if in the range ``0.0``–``4.0``.
    - Ignores values outside the valid range.

    :param val: GPA value to clean.
    :type val: str | float | None
    :return: Validated GPA value.
    :rtype: float | None
    """                                
    g = to_float(val)                               # Convert GPA value to float
    if g is None:                                   # If there is no value, return "None"
        return None                             
    return g if 0.0 <= g <= 4.0 else None           # Return the GPA as a float if it is within the 1.0 - 4.0 range (Including 5 skews data)

def clean_gre(val, kind):
    """
    Validate and normalize GRE scores.

    - For quantitative/verbal (``kind="qv"``): valid range is ``130``–``170``.
    - For analytical writing (``kind="aw"``): valid range is ``0.0``–``6.0``.

    :param val: GRE score to clean.
    :type val: str | float | None
    :param kind: GRE type: ``"qv"`` for quantitative/verbal, ``"aw"`` for analytical writing.
    :type kind: str
    :return: Validated GRE score.
    :rtype: float | None
    """
    s = to_float(val)                               # Convert GRE score to float
    if s is None:
        return None                                 # if there if no score, return "None"
    if kind == "aw":
        return s if 0.0 <= s <= 6.0 else None       # If the GRE analytical writing score is outside of the normal range, ignore
    return s if 130 <= s <= 170 else None           # If the GRE quantative/verbal score is outside of the normal range, ignore

def extract_data(item, idx):
    """
    Extract and normalize applicant data from a raw JSON record.

    Attempts to build a structured tuple corresponding to database
    fields, performing type cleaning for GPA, GRE, and dates.

    :param item: Applicant JSON record.
    :type item: dict
    :param idx: Fallback index used if a primary key cannot be derived.
    :type idx: int
    :return: Extracted applicant data as a tuple aligned with table schema.
    :rtype: tuple
    """
    url = item.get("url") or item.get("applicant_URL")  # Obtain the current applicant url

    # Use the URL to create a unique "p_id" value
    p_id = None
    if url:
        try:
            p_id = int(url.rstrip("/").split("/")[-1])  # Remove irrelevant url pieces
        except ValueError:
            pass

    if p_id is None:
        p_id = int(item.get("p_id", idx))               # If the previous code does not actually create a p_id, default to the loop index

    return (
        p_id,                                           # Primary key uses p_id unless it's missing, otherwise uses the loop index
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

def main(path=None):
    """
    Load processed applicant data into the PostgreSQL database.

    - Reads items from a JSON or JSON-lines file.
    - Extracts fields into structured tuples.
    - Creates the ``applicants`` table if it does not exist.
    - Inserts rows, ignoring conflicts on ``p_id``.

    :param path: Optional path to the LLM JSON file. Defaults to ``LLM_JSON``.
    :type path: str | None
    :return: None
    :rtype: NoneType
    """
    llm_file = path or LLM_JSON         # Fallback to default file name when this is ran as a standalone script
    llm_items = read_items(llm_file)

    rows = []
    for i, item in enumerate(llm_items):
        rows.append(extract_data(item, i + 1))

    with connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.executemany(INSERT_SQL, rows)
        conn.commit()

    print(f"Pushed {len(rows)} rows into applicants.")

if __name__ == "__main__":  # pragma: no cover
    main()
