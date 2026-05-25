"""
Chicago Building Violations API — Application Package
======================================================
Flask application factory with route registration and Swagger UI.
"""

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint


# Swagger UI configuration
SWAGGER_URL = "/docs"
API_URL = "/static/openapi.json"


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    # Register API routes
    from app.routes import register_routes
    register_routes(app)

    # Register Swagger UI blueprint
    swagger_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "Chicago Building Violations API"}
    )
    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)

    return app
