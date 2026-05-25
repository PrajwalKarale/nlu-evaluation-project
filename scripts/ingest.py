"""
Ingestion Script for Chicago Building Violations & Scofflaw Data
================================================================
Reads two CSV datasets, transforms them, and bulk-inserts into
a PostgreSQL database (Supabase).

Usage:
    python scripts/ingest.py

Prerequisites:
    - .env file with DATABASE_URL (see .env.example)
    - pip install -r requirements.txt
    - CSV files in datasets/ directory
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env from project root (one level up from scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment.")
    print("Create a .env file with your Supabase connection string.")
    print("See .env.example for the format.")
    sys.exit(1)

VIOLATIONS_CSV = os.path.join(PROJECT_ROOT, "datasets", "Building_Violations_20250815.csv")
SCOFFLAWS_CSV = os.path.join(PROJECT_ROOT, "datasets", "Building_Code_Scofflaw_List_20250807.csv")


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def normalize_address(address):
    """Normalize an address for reliable JOIN operations."""
    if pd.isna(address) or address is None:
        return ""
    return str(address).strip().upper()


# ---------------------------------------------------------------------------
# Step 1: Create Tables
# ---------------------------------------------------------------------------

def create_tables(cur):
    """Drop and recreate all tables."""
    print("Creating tables...")

    cur.execute("DROP TABLE IF EXISTS comments;")
    cur.execute("DROP TABLE IF EXISTS violations;")
    cur.execute("DROP TABLE IF EXISTS scofflaws;")

    cur.execute("""
        CREATE TABLE violations (
            id              INTEGER PRIMARY KEY,
            violation_date  DATE NOT NULL,
            violation_code  TEXT NOT NULL,
            violation_status TEXT NOT NULL,
            violation_description TEXT,
            inspector_comments TEXT,
            address         TEXT NOT NULL,
            address_norm    TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE scofflaws (
            record_id       TEXT PRIMARY KEY,
            address         TEXT NOT NULL,
            address_norm    TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE comments (
            id              SERIAL PRIMARY KEY,
            address         TEXT NOT NULL,
            address_norm    TEXT NOT NULL,
            author          TEXT NOT NULL,
            comment         TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT NOW()
        );
    """)

    print("  ✓ Tables created")


# ---------------------------------------------------------------------------
# Step 2: Ingest Violations
# ---------------------------------------------------------------------------

def ingest_violations(cur):
    """Read, transform, and insert violations data."""
    print(f"\nIngesting violations from {os.path.basename(VIOLATIONS_CSV)}...")

    # Read only the columns we need (7 of 25)
    df = pd.read_csv(
        VIOLATIONS_CSV,
        usecols=[
            "ID",
            "VIOLATION DATE",
            "VIOLATION CODE",
            "VIOLATION STATUS",
            "VIOLATION DESCRIPTION",
            "VIOLATION INSPECTOR COMMENTS",
            "ADDRESS"
        ]
    )

    # Rename columns to match DB schema (use dict to avoid column order issues)
    df = df.rename(columns={
        "ID": "id",
        "VIOLATION DATE": "violation_date",
        "VIOLATION CODE": "violation_code",
        "VIOLATION STATUS": "violation_status",
        "VIOLATION DESCRIPTION": "violation_description",
        "VIOLATION INSPECTOR COMMENTS": "inspector_comments",
        "ADDRESS": "address"
    })

    # Normalize address for JOIN
    df["address_norm"] = df["address"].apply(normalize_address)

    # Convert date: MM/DD/YYYY → YYYY-MM-DD
    df["violation_date"] = pd.to_datetime(
        df["violation_date"], format="%m/%d/%Y"
    ).dt.strftime("%Y-%m-%d")

    # Replace NaN with None (Postgres NULL)
    df = df.where(pd.notnull(df), None)

    # Ensure column order matches INSERT statement
    df = df[["id", "violation_date", "violation_code", "violation_status",
             "violation_description", "inspector_comments", "address", "address_norm"]]

    # Convert to list of tuples for bulk insert
    tuples = list(df.itertuples(index=False, name=None))

    # Bulk insert using execute_values (fastest psycopg2 method)
    execute_values(
        cur,
        """
        INSERT INTO violations
            (id, violation_date, violation_code, violation_status,
             violation_description, inspector_comments, address, address_norm)
        VALUES %s
        """,
        tuples,
        page_size=1000
    )

    print(f"  ✓ Ingested {len(tuples):,} violations")
    return len(tuples)


# ---------------------------------------------------------------------------
# Step 3: Ingest Scofflaws
# ---------------------------------------------------------------------------

def ingest_scofflaws(cur):
    """Read, transform, and insert scofflaw data."""
    print(f"\nIngesting scofflaws from {os.path.basename(SCOFFLAWS_CSV)}...")

    # Read only the columns we need (2 of 16)
    df = pd.read_csv(
        SCOFFLAWS_CSV,
        usecols=["RECORD ID", "ADDRESS"]
    )

    # Rename columns to match DB schema (use dict to avoid order issues)
    df = df.rename(columns={
        "RECORD ID": "record_id",
        "ADDRESS": "address"
    })

    # Clean and de-duplicate keys to avoid primary key violations
    df["record_id"] = df["record_id"].astype(str).str.strip()
    before = len(df)
    df = df.dropna(subset=["record_id"])
    df = df[df["record_id"] != ""]
    df = df.drop_duplicates(subset=["record_id"], keep="first")
    dropped = before - len(df)
    if dropped:
        print(f"  • Dropped {dropped:,} duplicate/blank RECORD ID rows")

    # Normalize address for JOIN
    df["address_norm"] = df["address"].apply(normalize_address)

    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    # Ensure column order matches INSERT statement
    df = df[["record_id", "address", "address_norm"]]

    # Convert to list of tuples
    tuples = list(df.itertuples(index=False, name=None))

    # Bulk insert with upsert to handle any remaining duplicates
    execute_values(
        cur,
        """
        INSERT INTO scofflaws (record_id, address, address_norm)
        VALUES %s
        ON CONFLICT (record_id) DO UPDATE
        SET address = EXCLUDED.address,
            address_norm = EXCLUDED.address_norm
        """,
        tuples,
        page_size=500
    )

    print(f"  ✓ Ingested {len(tuples):,} scofflaws")
    return len(tuples)


# ---------------------------------------------------------------------------
# Step 4: Create Indexes
# ---------------------------------------------------------------------------

def create_indexes(cur):
    """Create indexes after bulk insert for better performance."""
    print("\nCreating indexes...")

    cur.execute("CREATE INDEX idx_violations_address_norm ON violations(address_norm);")
    cur.execute("CREATE INDEX idx_violations_date ON violations(violation_date);")
    cur.execute("CREATE INDEX idx_violations_addr_date ON violations(address_norm, violation_date);")
    cur.execute("CREATE INDEX idx_scofflaws_address_norm ON scofflaws(address_norm);")
    cur.execute("CREATE INDEX idx_comments_address_norm ON comments(address_norm);")

    print("  ✓ Indexes created")


# ---------------------------------------------------------------------------
# Step 5: Verify
# ---------------------------------------------------------------------------

def verify(cur):
    """Print summary statistics to confirm successful ingestion."""
    print("\nVerifying...")

    cur.execute("SELECT COUNT(*) FROM violations;")
    v_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM scofflaws;")
    s_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT address_norm) FROM scofflaws;")
    unique_scofflaw_addrs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT address_norm) FROM violations;")
    unique_violation_addrs = cur.fetchone()[0]

    # Test the JOIN — how many scofflaw addresses also have violations?
    cur.execute("""
        SELECT COUNT(DISTINCT s.address_norm)
        FROM scofflaws s
        INNER JOIN violations v ON v.address_norm = s.address_norm;
    """)
    overlap = cur.fetchone()[0]

    print(f"  violations:              {v_count:,} rows")
    print(f"  scofflaws:               {s_count:,} rows")
    print(f"  unique violation addrs:  {unique_violation_addrs:,}")
    print(f"  unique scofflaw addrs:   {unique_scofflaw_addrs}")
    print(f"  scofflaw+violation join:  {overlap} addresses overlap")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("Chicago Building Violations — Data Ingestion")
    print("=" * 60)

    # Verify CSV files exist
    for path in [VIOLATIONS_CSV, SCOFFLAWS_CSV]:
        if not os.path.exists(path):
            print(f"ERROR: CSV file not found: {path}")
            sys.exit(1)

    # Connect to database
    print(f"\nConnecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()
    print("  ✓ Connected")

    try:
        create_tables(cur)
        conn.commit()

        ingest_violations(cur)
        conn.commit()

        ingest_scofflaws(cur)
        conn.commit()

        create_indexes(cur)
        conn.commit()

        verify(cur)

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: Ingestion failed: {e}")
        sys.exit(1)

    finally:
        cur.close()
        conn.close()

    print("\n" + "=" * 60)
    print("✓ Database ready")
    print("=" * 60)


if __name__ == "__main__":
    main()
