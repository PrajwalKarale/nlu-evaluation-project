"""
API route handlers.
Defines all public endpoints for the Chicago Building Violations API.
"""

from flask import request, jsonify, render_template
from app.db import get_connection, get_cursor, normalize_address
from app.validators import is_valid_date, sanitize_string


def register_routes(app):
    """Register all route handlers on the Flask app."""

    @app.route("/", methods=["GET"])
    def index():
        """Serve the single-page UI."""
        return render_template("index.html")

    @app.route("/property/<path:address>/", methods=["GET"])
    def get_property(address):
        """
        GET /property/<address>/

        Returns property violation information and scofflaw status.
        404 if address not found in either table.
        """
        addr_norm = normalize_address(address)

        if not addr_norm:
            return jsonify({"error": "Address is required"}), 400

        conn = get_connection()
        cur = get_cursor(conn)

        try:
            # Get all violations for this address
            cur.execute(
                """
                SELECT violation_date, violation_code, violation_status,
                       violation_description, inspector_comments
                FROM violations
                WHERE address_norm = %s
                """,
                (addr_norm,)
            )
            violations = cur.fetchall()

            # Check scofflaw status
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM scofflaws WHERE address_norm = %s)",
                (addr_norm,)
            )
            is_scofflaw = cur.fetchone()["exists"]

            # If no violations and not a scofflaw, address not found
            if not violations and not is_scofflaw:
                return jsonify({"error": "Address not found"}), 404

            # Build response
            violation_count = len(violations)
            last_violation_date = None
            violation_list = []

            if violations:
                # Find the most recent violation date
                dates = [v["violation_date"] for v in violations if v["violation_date"]]
                if dates:
                    last_violation_date = max(dates).strftime("%Y-%m-%d")

                # Build violations array
                for v in violations:
                    violation_list.append({
                        "date": v["violation_date"].strftime("%Y-%m-%d") if v["violation_date"] else None,
                        "code": v["violation_code"],
                        "status": v["violation_status"],
                        "description": v["violation_description"],
                        "inspector_comments": v["inspector_comments"]
                    })

            response = {
                "address": addr_norm,
                "last_violation_date": last_violation_date,
                "violation_count": violation_count,
                "violations": violation_list,
                "SCOFFLAW": is_scofflaw
            }

            return jsonify(response), 200

        finally:
            cur.close()
            conn.close()

    @app.route("/property/<path:address>/comments/", methods=["POST"])
    def post_comment(address):
        """
        POST /property/<address>/comments/

        Accepts JSON body: {"author": "...", "comment": "..."}
        Stores comment in the comments table.
        Returns 201 Created with success message.
        """
        addr_norm = normalize_address(address)

        if not addr_norm:
            return jsonify({"error": "Address is required"}), 400

        # Parse JSON body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Extract and sanitize fields
        author = sanitize_string(data.get("author"), max_length=200)
        comment = sanitize_string(data.get("comment"), max_length=5000)

        # Validate required fields
        if not author:
            return jsonify({"error": "author is required and cannot be empty"}), 400
        if not comment:
            return jsonify({"error": "comment is required and cannot be empty"}), 400

        conn = get_connection()
        cur = get_cursor(conn)

        try:
            # Validate that address exists in our database
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM violations WHERE address_norm = %s
                    UNION
                    SELECT 1 FROM scofflaws WHERE address_norm = %s
                )
                """,
                (addr_norm, addr_norm)
            )
            if not cur.fetchone()["exists"]:
                return jsonify({"error": "Address not found in database"}), 404

            cur.execute(
                """
                INSERT INTO comments (address, address_norm, author, comment)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (address.strip(), addr_norm, author, comment)
            )
            result = cur.fetchone()
            conn.commit()

            return jsonify({
                "message": "Comment created successfully",
                "id": result["id"],
                "created_at": result["created_at"].isoformat()
            }), 201

        finally:
            cur.close()
            conn.close()

    @app.route("/property/scofflaws/violations", methods=["GET"])
    def get_scofflaw_violations():
        """
        GET /property/scofflaws/violations?since=<yyyy-mm-dd>

        Returns array of scofflaw property addresses that had violations
        on or after the given date.
        """
        since = request.args.get("since")

        if not since:
            return jsonify({"error": "Query parameter 'since' is required (format: YYYY-MM-DD)"}), 400

        if not is_valid_date(since):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        conn = get_connection()
        cur = get_cursor(conn)

        try:
            cur.execute(
                """
                SELECT DISTINCT s.address
                FROM scofflaws s
                INNER JOIN violations v ON v.address_norm = s.address_norm
                WHERE v.violation_date >= %s
                """,
                (since,)
            )
            rows = cur.fetchall()

            addresses = [row["address"] for row in rows]

            return jsonify({
                "since": since,
                "count": len(addresses),
                "addresses": addresses
            }), 200

        finally:
            cur.close()
            conn.close()
