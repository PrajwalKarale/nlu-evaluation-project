"""
Response and request models for the API.
Defines the data contracts between the database layer and API layer.
Uses dataclasses for structured, self-documenting response construction.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Violation:
    """A single building violation record."""
    date: Optional[str]
    code: str
    status: str
    description: Optional[str]
    inspector_comments: Optional[str]


@dataclass
class PropertyResponse:
    """Response model for GET /property/<address>/"""
    address: str
    last_violation_date: Optional[str]
    violation_count: int
    violations: list
    SCOFFLAW: bool

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CommentResponse:
    """Response model for POST /property/<address>/comments/"""
    message: str
    id: int
    created_at: str

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ScofflawResponse:
    """Response model for GET /property/scofflaws/violations"""
    since: str
    count: int
    addresses: list

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ErrorResponse:
    """Standard error response model."""
    error: str

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
