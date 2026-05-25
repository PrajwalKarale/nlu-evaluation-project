"""
Entry point for the Chicago Building Violations API.

Usage:
    Development:  python run.py
    Production:   gunicorn "run:app"
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
