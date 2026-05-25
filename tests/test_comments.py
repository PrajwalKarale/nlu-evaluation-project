"""
Tests for POST /property/<address>/comments/
"""

import psycopg2


def test_post_comment_success(client):
    """Valid comment returns 201 with message, id, and created_at."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        json={"author": "jdoe", "comment": "looks bad"}
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "message" in data
    assert "id" in data
    assert "created_at" in data


def test_post_comment_persists(client, test_db):
    """Comment is actually written to the database."""
    client.post(
        "/property/100 N MAIN ST/comments/",
        json={"author": "jdoe", "comment": "looks bad"}
    )

    conn = psycopg2.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT author, address_norm FROM comments WHERE author='jdoe'")
    row = cur.fetchone()
    cur.close()
    conn.close()

    assert row is not None
    assert row[0] == "jdoe"
    assert row[1] == "100 N MAIN ST"


def test_post_comment_missing_author(client):
    """Missing author field returns 400."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        json={"comment": "x"}
    )
    assert resp.status_code == 400


def test_post_comment_missing_comment(client):
    """Missing comment field returns 400."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        json={"author": "a"}
    )
    assert resp.status_code == 400


def test_post_comment_empty_comment(client):
    """Whitespace-only comment returns 400 (sanitized to empty)."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        json={"author": "a", "comment": "   "}
    )
    assert resp.status_code == 400


def test_post_comment_strips_control_chars(client, test_db):
    """Control characters are removed from comment before storage."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        json={"author": "a", "comment": "hi\x00\x01\x07there"}
    )
    assert resp.status_code == 201

    conn = psycopg2.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT comment FROM comments ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()

    assert row[0] == "hithere"


def test_post_comment_invalid_json(client):
    """Non-JSON body returns 400."""
    resp = client.post(
        "/property/100 N MAIN ST/comments/",
        data="not json",
        content_type="text/plain"
    )
    assert resp.status_code == 400


def test_post_comment_unknown_address(client):
    """Comment on an address not in violations or scofflaws returns 404."""
    resp = client.post(
        "/property/999 FAKE STREET/comments/",
        json={"author": "test", "comment": "this should fail"}
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data
