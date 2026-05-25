"""
Tests for GET /property/scofflaws/violations?since=<yyyy-mm-dd>
"""


def test_scofflaws_since_valid(client):
    """Returns scofflaw addresses with violations after the given date."""
    resp = client.get("/property/scofflaws/violations?since=2024-01-01")
    assert resp.status_code == 200
    data = resp.get_json()

    addresses = data["addresses"]
    # 100 N MAIN ST is a scofflaw with violations (dates: 2024-05-10, 2024-06-12, 2025-08-01)
    assert "100 N MAIN ST" in addresses
    # 200 W OAK AVE is a scofflaw with a violation (date: 2024-12-01)
    assert "200 W OAK AVE" in addresses
    # 300 S ELM ST is a scofflaw but has NO violations
    assert "300 S ELM ST" not in addresses
    # 999 W LAKE ST has violations but is NOT a scofflaw
    assert "999 W LAKE ST" not in addresses

    assert data["count"] == 2
    assert data["since"] == "2024-01-01"


def test_scofflaws_since_filters_by_date(client):
    """A later date filters out older violations."""
    resp = client.get("/property/scofflaws/violations?since=2025-01-01")
    assert resp.status_code == 200
    data = resp.get_json()

    addresses = data["addresses"]
    # Only 100 N MAIN ST has a violation on 2025-08-01
    assert "100 N MAIN ST" in addresses
    # 200 W OAK AVE's violation is 2024-12-01 — before 2025-01-01
    assert "200 W OAK AVE" not in addresses
    assert data["count"] == 1


def test_scofflaws_since_future_date(client):
    """Future date returns empty array."""
    resp = client.get("/property/scofflaws/violations?since=2099-01-01")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["addresses"] == []
    assert data["count"] == 0


def test_scofflaws_since_missing_param(client):
    """Missing 'since' query parameter returns 400."""
    resp = client.get("/property/scofflaws/violations")
    assert resp.status_code == 400


def test_scofflaws_since_bad_format_text(client):
    """Non-date string returns 400."""
    resp = client.get("/property/scofflaws/violations?since=not-a-date")
    assert resp.status_code == 400


def test_scofflaws_since_bad_format_slashes(client):
    """Wrong date format (slashes) returns 400."""
    resp = client.get("/property/scofflaws/violations?since=2024/01/01")
    assert resp.status_code == 400
