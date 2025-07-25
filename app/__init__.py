"""Application factory and shared extensions."""

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

from .config import config

db = SQLAlchemy()

def create_app(config_name: str = "development") -> Flask:
    """Create and configure a Flask application."""
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    app.config.from_object(config[config_name])
    app.config.setdefault("SESSION_TYPE", "filesystem")

    Session(app)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


    db.init_app(app)
    # Note: Database tables are now managed by Alembic migrations
    # Run 'python db_utils/manage_migrations.py upgrade' to apply migrations
    return app

