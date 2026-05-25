"""
Tests for GET /property/<address>/
"""


def test_property_404_unknown_address(client):
    """Address not in either table returns 404."""
    resp = client.get("/property/123 NOWHERE ST/")
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data


def test_property_200_violations_and_scofflaw(client):
    """Address with violations AND scofflaw status returns full data."""
    resp = client.get("/property/100 N MAIN ST/")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["violation_count"] == 3
    assert data["last_violation_date"] == "2025-08-01"
    assert data["SCOFFLAW"] is True
    assert len(data["violations"]) == 3

    # Each violation has required fields
    for v in data["violations"]:
        assert "date" in v
        assert "code" in v
        assert "status" in v
        assert "description" in v
        assert "inspector_comments" in v


def test_property_200_scofflaw_no_violations(client):
    """Address is a scofflaw but has no violations — still returns 200."""
    resp = client.get("/property/300 S ELM ST/")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["SCOFFLAW"] is True
    assert data["violation_count"] == 0
    assert data["violations"] == []
    assert data["last_violation_date"] is None


def test_property_200_violations_no_scofflaw(client):
    """Address has violations but is NOT a scofflaw."""
    resp = client.get("/property/999 W LAKE ST/")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["SCOFFLAW"] is False
    assert data["violation_count"] == 2


def test_property_address_case_insensitive(client):
    """Lowercase address input still matches (normalization works)."""
    resp = client.get("/property/100 n main st/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["violation_count"] == 3


def test_property_address_with_whitespace(client):
    """Extra whitespace in address is trimmed before lookup."""
    resp = client.get("/property/  100 N MAIN ST  /")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["violation_count"] == 3
