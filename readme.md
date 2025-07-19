# Requirements Management Tool

A Flask-based web application for managing requirements with hierarchical groups and Excel import/export.


## Requirements

- **Requirement Management**: Create requirements with unique IDs, titles, descriptions, status, chapter, and group assignment
- **Requirement Endpoints**: Perform CRUD operations on individual or batches of requirements
- **Hierarchical Requirements Management**: Organize requirements in groups with parent-child relationships
- **Change Tracking**: Log changes to requirement fields with user, timestamp, old and new values
- **Batch Operations**: Support batch updates of requirements with field validation
- **Text Field**: Requiremnt text field shal support either markdown or WYSIWYG including pictures
- **Chat**: Each requirment shall have separate chat.

- **Group Management**: Manage hierarchical groups with parent-child relationships and track creation/update times
- **Group Endpoints**: Create, update, retrieve, and delete groups via API

- **Excel Import/Export**: Upload Excel files and export requirements

- **User Management**: Register users and store usernames, hashed passwords, emails, active status, and timestamps
- **Authentication**: Authenticate users via a login endpoint and assign session IDs

- **User Interface**: Provide dashboard, searchable/filterable requirement table, graph view, and modals for editing

- **Graph Visualization**: Display parent-child requirement links in a visual graph with status-based colors
- **Node Positioning**: Allow users to update and persist node positions via API

- **Status automations**: When req changed the status back to draft
- **Req review process automation**: System shall allow requrment review process by alloving selection of reviwer and allowinf status to change from draft to accepted only when all accepted.



## Project Structure

```
req_mng_tool/
├── app/                    # Main application
│   ├── app.py             # Flask application
│   ├── config.py          # Configuration
│   ├── models.py          # Database models
│   ├── __init__.py        # App factory and DB setup
│   ├── static/            # Static files (CSS, JS)
│   └── templates/         # HTML templates
├── db_utils/              # Database utility scripts
│   └── create_sample_excel.py # Sample data creation
├── docker-compose.yml     # Docker orchestration
├── start_dev.bat          # Windows development script
├── start_dev.sh           # Linux/macOS development script
└── uploads/              # File uploads directory
```
 - **`app/`**: Main application code, templates, and database models
 - **`db_utils/`**: Database utility scripts
 - **Root**: Configuration and orchestration files

## Deployment Methods

### Method 1: Full Docker Compose Deployment

**For production or complete containerized deployment:**

```bash
# Start all services (Flask app and PostgreSQL)
docker-compose up --build

# Access the application:
# - Main app: http://localhost:5000
```

### Method 2: Hybrid Local Development (Recommended)

You can run the Flask app locally and the database in Docker. Use the provided scripts for your OS:

#### On **Windows**
```bat
start_dev.bat
```
- Activates the virtual environment
- Sets environment variables
- Starts the Postgres database via Docker Compose
- Runs the Flask app

#### On **Linux/macOS**
```bash
./start_dev.sh
```
- Activates the virtual environment
- Sets environment variables
- Starts the Postgres database via Docker Compose
- Runs the Flask app

**Manual steps (if you don't use the scripts):**
```bash
# 1. Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set environment variables (see .env.example)
export DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng
export FLASK_ENV=development
export SECRET_KEY=your-secret-key

# 3. Start database service only
docker-compose up -d postgres

# 4. Run Flask app locally
python -m app.app

# Access: http://localhost:5000
```

## Environment Variables

Create a `.env` file or use the provided scripts. Example:

```env
DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## Development

### Local Development Setup
1. Use Method 2 (Hybrid Deployment)
2. Make changes to files in `app/` directory
3. Flask app auto-reloads on file changes
4. Database tables are auto-created on startup

### Reset Everything
```bash
docker-compose down -v
docker-compose up --build
```

### Rebuild image
```bash
docker-compose up --build --force-recreate
```

