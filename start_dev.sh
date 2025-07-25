#!/bin/bash

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "No venv directory found. Please create a virtual environment and install requirements."
    exit 1
fi

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found. Please copy env.example to .env and configure it."
    exit 1
fi

echo "Environment variables set for local development."
echo "DATABASE_URL: $DATABASE_URL"
echo "FLASK_ENV: $FLASK_ENV"

echo "Starting Postgres via Docker Compose..."
docker-compose up -d postgres
if [ $? -ne 0 ]; then
    echo "Failed to start Postgres with Docker Compose."
    exit 1
fi

echo "Waiting for Postgres to initialize..."
sleep 8

echo "Applying database migrations..."
python db_utils/manage_migrations.py upgrade
if [ $? -ne 0 ]; then
    echo "Failed to apply database migrations."
    exit 1
fi

echo "Starting Flask app..."
python -m app.app 