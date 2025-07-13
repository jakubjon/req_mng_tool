# Requirements Management Tool

A Flask-based web application for managing requirements with hierarchical groups, Excel import/export, and Directus CMS integration.

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
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r app/requirements.txt

# 2. Set environment variables
.\setup-env.ps1

# 3. Start database services only
docker-compose up -d postgres directus

# 4. Run Flask app locally
python app/app.py

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

## Features

- **Hierarchical Requirements Management**: Organize requirements in groups with parent-child relationships
- **Excel Import/Export**: Upload Excel files and export requirements
- **Change Tracking**: Track all changes to requirements with history
- **Directus Integration**: Headless CMS for content management
- **RESTful API**: Full API for programmatic access
- **Responsive UI**: Modern web interface

## Development

### Local Development Setup
1. Use Method 2 (Hybrid Deployment)
2. Make changes to files in `app/` directory
3. Flask app auto-reloads on file changes
4. Database changes require running init/reset scripts

### File Structure
- **`app/`**: Main application code and templates
- **`db_mng/`**: Database management and utility scripts
- **Root**: Configuration and orchestration files

## Troubleshooting

### Common Issues
1. **Import errors**: Make sure you're running from project root
2. **Database connection**: Ensure PostgreSQL container is running
3. **Port conflicts**: Check if ports 5000, 8055, 5432 are available

### Reset Everything
```bash
docker-compose down -v
docker-compose up --build
```