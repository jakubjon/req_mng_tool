#!/bin/bash

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "No venv directory found. Please create a virtual environment and install requirements."
    exit 1
fi

# Set environment variables
export DATABASE_URL="postgresql://reqmng:reqmng@localhost:5432/reqmng"
export FLASK_ENV=development
export FLASK_DEBUG=1
export SECRET_KEY="dev-secret-key-change-in-production"

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

echo "Starting Flask app..."
python -m app.app 