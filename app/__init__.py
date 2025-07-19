"""Application factory and shared extensions."""

from flask import Flask
from flask_cors import CORS
from flask_session import Session
import os
from dotenv import load_dotenv

from .config import config
from db import db, init_app as init_db


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

    init_db(app)
    return app

