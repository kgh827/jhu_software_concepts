# Getting Started

This project scrapes, cleans, stores, and analyzes graduate admissions data from Grad Café, exposing results through a Flask web interface and supporting queries in PostgreSQL.

## Prerequisites
- Python 3.10+ (recommended)
- PostgreSQL running locally or remotely
- A virtual environment (venv)

## Setup

```powershell
# Clone repository
git clone <your-repo-url>
cd jhu_software_concepts/module_4

# Create and activate venv
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Set database connection string (example)
$env:DATABASE_URL="postgresql://user:pass@localhost:5432/gradcafe"
