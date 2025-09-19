# Architecture

The system is organized around six major components.

## 1. Scraping
- **File:** `src/scrape.py`  
- Uses `urllib3` + `BeautifulSoup` to extract applicant rows from Grad Café tables.  
- Converts raw HTML into structured dictionaries.

## 2. Cleaning
- **File:** `src/clean.py`  
- Normalizes GPA, GRE, program/university names, and status fields.  
- Produces schema-ready records.

## 3. Loading & Database
- **Files:** `src/load_data.py`, `src/db.py`  
- Reads cleaned/LLM-enriched data and inserts into PostgreSQL (`applicants` table).  
- Handles schema creation, idempotent inserts, and basic counts.

## 4. Querying & Analysis
- **File:** `src/query_data.py`  
- Aggregates stats: totals, term filters, international %, GPA/GRE means, acceptance %, degree histograms, top universities.  
- Returns a dictionary the web layer renders.

## 5. Web Application
- **File:** `src/flask_app.py`  
- Flask routes:
  - `/` — render analysis dashboard  
  - `/pull_data` — kick off scrape → clean → LLM → load (background)  
  - `/update_analysis` — refresh view when scraping isn’t running

## 6. Tests
- **Folder:** `tests/`  
- Unit + integration tests with `pytest` and custom markers (`db`, `scraper`, `web`, `analysis`, `integration`).  
- Heavy use of monkeypatching to avoid real network/DB calls and to keep tests fast.
