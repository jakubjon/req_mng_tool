@echo off
REM Activate virtual environment
if exist .\venv\Scripts\Activate.ps1 (
    call powershell -ExecutionPolicy Bypass -File .\venv\Scripts\Activate.ps1
    echo Virtual environment activated.
) else (
    echo No venv directory found. Please create a virtual environment and install requirements.
    exit /b 1
)

REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env file...
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
) else (
    echo .env file not found. Please copy env.example to .env and configure it.
    exit /b 1
)

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

echo Applying database migrations...
python db_utils/manage_migrations.py upgrade
if errorlevel 1 (
    echo Failed to apply database migrations.
    exit /b 1
)

echo Starting Flask app...
python -m app.app 