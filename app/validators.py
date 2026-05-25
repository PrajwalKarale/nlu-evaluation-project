"""
Input validation and sanitization helpers.
"""

import re
from datetime import datetime

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_date(date_str):
    """Validate that a string is a valid YYYY-MM-DD date."""
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def sanitize_string(value, max_length=1000):
    """
    Basic input sanitization for user-submitted strings.
    - Strip leading/trailing whitespace
    - Remove control characters
    - Enforce max length
    """
    if not value or not isinstance(value, str):
        return None
    # Strip whitespace
    value = value.strip()
    # Remove control characters (keep printable + newlines)
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    # Enforce max length
    if len(value) > max_length:
        value = value[:max_length]
    return value if value else None
