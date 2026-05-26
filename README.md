# Chicago Building Violations Explorer

A backend API service that processes City of Chicago building violation and scofflaw data, joined by address to surface meaningful property information.

## Live Demo

🔗 **[Live Link](https://nlu-building-violations.onrender.com)** *(update with actual URL after deployment)*

---

## Architecture

```
┌──────────────┐         ┌─────────────────────┐
│  Flask App   │────────▶│  Supabase PostgreSQL │
│  (Render)    │◀────────│  (Cloud Database)    │
└──────────────┘         └─────────────────────┘
```

| Component | Technology | Purpose |
|---|---|---|
| Web Framework | Flask (Python) | API endpoints + UI |
| Database | PostgreSQL (Supabase) | Data storage, JOINs, queries |
| DB Driver | psycopg2 | Raw SQL, parameterized queries (no ORM) |
| Ingestion | Pandas + psycopg2 | CSV parsing, transformation, bulk insert |
| Deployment | Render (free tier) | Hosting the Flask app |

## Design Decisions

- **No ORM** — All database access uses raw SQL with parameterized queries via psycopg2. This satisfies the project constraint and gives full control over query optimization.
- **Address normalization** — Both tables store an `address_norm` column (UPPER + TRIM) to enable reliable JOINs. The original address is preserved for display.
- **Indexes created after bulk insert** — Faster ingestion; indexes are built once on the final dataset.
- **Composite index** on `(address_norm, violation_date)` — Optimizes the scofflaw-violations JOIN + date filter query.
- **Minimal columns** — Only fields required by the API endpoints are ingested. This keeps the schema focused and easy to review.
- **Pandas for ingestion** — Handles date parsing, null handling, and column selection concisely. The `execute_values` method provides fast bulk inserts.

---

## Running Locally

### Prerequisites

- Python 3.9+
- A Supabase account (free tier) or any PostgreSQL database

### Quick Setup (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/nlu-building-violations.git
cd nlu-building-violations

# Edit .env with your Supabase/PostgreSQL connection string
cp .env.example .env
# Set DATABASE_URL in .env

# Run the setup script (installs deps, loads data)
chmod +x setup.sh
./setup.sh
```

The setup script handles everything: virtual environment, dependencies, and data ingestion.

### Manual Setup

If you prefer to run each step manually:

```bash
git clone https://github.com/YOUR_USERNAME/nlu-building-violations.git
cd nlu-building-violations

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database connection
cp .env.example .env
# Edit .env with your Supabase/PostgreSQL connection string

# Run data ingestion
python scripts/ingest.py
```

### Ingest Data

```bash
python scripts/ingest.py
```

Expected output:
```
============================================================
Chicago Building Violations — Data Ingestion
============================================================
Connecting to database...
  ✓ Connected
Creating tables...
  ✓ Tables created
Ingesting violations...
  ✓ Ingested 77,492 violations
Ingesting scofflaws...
  ✓ Ingested 555 scofflaws
Creating indexes...
  ✓ Indexes created
Verifying...
  violations:              77,492 rows
  scofflaws:               555 rows
  unique violation addrs:  15,888
  unique scofflaw addrs:   256
  scofflaw+violation join:  27 addresses overlap
============================================================
✓ Database ready
============================================================
```

### Start the Server

```bash
python run.py
```

Open http://localhost:5000 in your browser.

### Run Tests

```bash
pytest tests/ -v
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/property/<address>/` | Property violations + scofflaw status |
| POST | `/property/<address>/comments/` | Add a comment to an address |
| GET | `/property/scofflaws/violations?since=YYYY-MM-DD` | Scofflaw addresses with violations since date |

See [api_documentation.md](api_documentation.md) for full request/response schemas.

---

## Project Structure

```
├── README.md                 ← This file
├── api_documentation.md      ← API JSON schema documentation
├── requirements.txt          ← Python dependencies
├── setup.sh                  ← One-command setup script
├── run.py                    ← Application entry point
├── .env.example              ← Environment variable template
├── .gitignore
│
├── app/                      ← Application package (separation of concerns)
│   ├── __init__.py           ← App factory (create_app)
│   ├── routes.py             ← API endpoint handlers
│   ├── db.py                 ← Database connection + helpers
│   └── validators.py         ← Input validation & sanitization
│
├── scripts/                  ← Standalone scripts
│   └── ingest.py             ← Data ingestion script (deliverable)
│
├── db/                       ← Database artifacts
│   └── schema.sql            ← CREATE TABLE SQL scripts (deliverable)
│
├── templates/
│   └── index.html            ← Single-page UI
│
├── static/
│   └── style.css             ← UI styles
│
├── datasets/
│   ├── Building_Violations_20250815.csv
│   └── Building_Code_Scofflaw_List_20250807.csv
│
└── tests/                    ← Test suite
    ├── conftest.py           ← Test fixtures & seed data
    ├── test_property.py      ← GET /property/<address>/ tests
    ├── test_comments.py      ← POST /property/<address>/comments/ tests
    └── test_scofflaws_since.py ← GET /property/scofflaws/violations tests
```

---

## Database Schema

Three tables (see [db/schema.sql](db/schema.sql) for full DDL):

- **violations** — Building violation records (77,492 rows, filtered to 2024+)
- **scofflaws** — Building code scofflaw list (555 rows)
- **comments** — User-submitted comments (populated via POST endpoint)

Tables are joined on `address_norm` (normalized address column).

---

## Data Sources

- [Building Violations](https://data.cityofchicago.org/Buildings/Building-Violations/22u3-xenr) — City of Chicago
- [Building Code Scofflaw List](https://data.cityofchicago.org/Buildings/Building-Code-Scofflaw-List/crg5-4zyp) — City of Chicago
