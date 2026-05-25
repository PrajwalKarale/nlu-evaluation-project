"""
Test fixtures for Chicago Building Violations API.

Sets up a test database with known seed data, provides a Flask test client.
Requires DATABASE_URL in .env pointing to a PostgreSQL database.
"""

import os
import sys
import pytest
import psycopg2

# Add project root to path so we can import the app package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def database_url():
    """Get the database URL from environment."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping integration tests")
    return url


@pytest.fixture()
def test_db(database_url):
    """
    Create test tables with known seed data.
    Drops and recreates tables before each test, cleans up after.
    """
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()

    # Create fresh tables
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

    # Create indexes
    cur.execute("CREATE INDEX idx_violations_address_norm ON violations(address_norm);")
    cur.execute("CREATE INDEX idx_scofflaws_address_norm ON scofflaws(address_norm);")
    cur.execute("CREATE INDEX idx_comments_address_norm ON comments(address_norm);")

    # Seed scofflaws (3 records, 3 unique addresses)
    cur.execute("""
        INSERT INTO scofflaws (record_id, address, address_norm) VALUES
        ('R1', '100 N MAIN ST', '100 N MAIN ST'),
        ('R2', '200 W OAK AVE', '200 W OAK AVE'),
        ('R3', '300 S ELM ST', '300 S ELM ST');
    """)

    # Seed violations (6 records across different addresses)
    cur.execute("""
        INSERT INTO violations (id, violation_date, violation_code, violation_status,
                               violation_description, inspector_comments, address, address_norm)
        VALUES
        (1, '2024-05-10', 'CN104035', 'OPEN', 'MAINTAIN WINDOW', 'BROKEN PANE', '100 N MAIN ST', '100 N MAIN ST'),
        (2, '2024-06-12', 'CN190019', 'COMPLIED', 'ARRANGE INSPECTION', 'OK', '100 N MAIN ST', '100 N MAIN ST'),
        (3, '2025-08-01', 'EV1110', 'OPEN', 'ELEV INSP', 'PENDING', '100 N MAIN ST', '100 N MAIN ST'),
        (4, '2024-04-15', 'CN061014', 'OPEN', 'PORCH', 'SAGGING', '999 W LAKE ST', '999 W LAKE ST'),
        (5, '2024-07-20', 'CN070024', 'COMPLIED', 'RAILING', 'REPAIRED', '999 W LAKE ST', '999 W LAKE ST'),
        (6, '2024-12-01', 'EV1111', 'OPEN', 'ELEV', 'OUT OF SERVICE', '200 W OAK AVE', '200 W OAK AVE');
    """)

    cur.close()
    conn.close()

    yield database_url

    # Cleanup: drop test tables after tests complete
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS comments;")
    cur.execute("DROP TABLE IF EXISTS violations;")
    cur.execute("DROP TABLE IF EXISTS scofflaws;")
    cur.close()
    conn.close()


@pytest.fixture()
def client(test_db):
    """
    Provide a Flask test client connected to the test database.
    """
    from app.db import set_database_url
    set_database_url(test_db)

    from app import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client
