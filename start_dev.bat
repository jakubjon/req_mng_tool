@echo off
REM Activate virtual environment
if exist .\venv\Scripts\Activate.ps1 (
    call powershell -ExecutionPolicy Bypass -File .\venv\Scripts\Activate.ps1
    echo Virtual environment activated.
) else (
    echo No venv directory found. Please create a virtual environment and install requirements.
    exit /b 1
)

REM Set environment variables
set DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng
set FLASK_ENV=development
set FLASK_DEBUG=1
set SECRET_KEY=dev-secret-key-change-in-production

echo Environment variables set for local development.
echo DATABASE_URL: %DATABASE_URL%
echo FLASK_ENV: %FLASK_ENV%

echo Starting Postgres via Docker Compose...
docker-compose up -d postgres
if errorlevel 1 (
    echo Failed to start Postgres with Docker Compose.
    exit /b 1
)

echo Waiting for Postgres to initialize...
TIMEOUT /T 8 /NOBREAK

echo Starting Flask app...
python -m app.app 