# Requirements Management Tool

A Flask-based web application for managing requirements with hierarchical groups, Excel import/export, and Directus CMS integration.


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
│   ├── models.py          # Database models
│   ├── config.py          # Configuration
│   ├── Dockerfile         # Docker configuration
│   ├── requirements.txt   # Python dependencies
│   ├── static/            # Static files (CSS, JS)
│   └── templates/         # HTML templates
├── db_mng/                # Database management scripts
│   ├── init_db.py         # Database initialization
│   ├── reset_db.py        # Database reset
│   └── create_sample_excel.py # Sample data creation
├── docker-compose.yml     # Docker orchestration
├── setup-env.ps1         # Environment setup script
└── uploads/              # File uploads directory
```
- **`app/`**: Main application code and templates
- **`db_mng/`**: Database management and utility scripts
- **Root**: Configuration and orchestration files

## Deployment Methods

### Method 1: Full Docker Compose Deployment

**For production or complete containerized deployment:**

```bash
# Start all services (Flask app, Directus, PostgreSQL)
docker-compose up --build

# Access the application:
# - Main app: http://localhost:5000
# - Directus CMS: http://localhost:8055 (admin@admin.com / admin123)
```

### Method 2: Hybrid Deployment (Recommended for Development)

**Flask app locally, database services in Docker:**

```bash
# 1. Set up Python environment
python3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r app/requirements.txt

# 2. Set environment variables
.\setup-env.ps1

# 3. Start database services only
docker-compose up -d postgres directus

# 4. Run Flask app locally
python -m app.app

# Access: http://localhost:5000
```

## Database Management

### Initialize Database
```bash
# From project root
python -m db_mng.init_db
```

### Reset Database
```bash
# From project root
python -m db_mng.reset_db
```

### Create Sample Data
```bash
# From project root
python -m db_mng.create_sample_excel
```

## Environment Variables

Create a `.env` file or use `setup-env.ps1`:

```env
DATABASE_URL=postgresql://directus:directus@localhost:5432/directus
DIRECTUS_URL=http://localhost:8055
FLASK_ENV=development
SECRET_KEY=your-secret-key
```


## Development

### Local Development Setup
1. Use Method 2 (Hybrid Deployment)
2. Make changes to files in `app/` directory
3. Flask app auto-reloads on file changes
4. Database changes require running init/reset scripts


### Reset Everything
```bash
docker-compose down -v
docker-compose up --build
```

