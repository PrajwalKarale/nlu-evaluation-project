"""
Database helper module.
Provides connection management and shared utilities.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Can be overridden for testing via set_database_url()
_database_url = os.getenv("DATABASE_URL")


def set_database_url(url):
    """Override the database URL (used by tests)."""
    global _database_url
    _database_url = url


def get_database_url():
    """Get the current database URL."""
    return _database_url


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(_database_url)


def get_cursor(conn):
    """Get a cursor that returns rows as dictionaries."""
    return conn.cursor(cursor_factory=RealDictCursor)


def normalize_address(address):
    """
    Normalize an address for reliable database lookups and JOINs.
    Applies: strip whitespace + convert to uppercase.
    """
    if not address:
        return ""
    return address.strip().upper()
