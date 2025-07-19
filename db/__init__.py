"""Database configuration and initialization utilities."""

from flask_sqlalchemy import SQLAlchemy

# Shared SQLAlchemy instance
# Import this in application modules and management scripts


# Create the database object
# Actual initialization with a Flask app occurs via init_app

db = SQLAlchemy()


def init_app(app):
    """Initialize the shared database with the given Flask app."""
    db.init_app(app)
