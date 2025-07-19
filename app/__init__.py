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
    app.config.setdefault("UPLOAD_FOLDER", "uploads")
    app.config.setdefault("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"))
    app.config.setdefault("SESSION_TYPE", "filesystem")

    Session(app)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app

