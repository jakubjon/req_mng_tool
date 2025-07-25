# Requirements Management Tool

A Flask-based web application for managing requirements with hierarchical groups and Excel import/export.


## Requirements

Requirments for this system are listed in req_for_reqmngtool.csv and are managable within the system itself.


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
│   ├── create_sample_excel.py # Sample data creation
│   └── manage_migrations.py   # Migration management script
├── docs/                  # Documentation files
│   ├── table_UI_notes.txt # UI development notes
│   └── Alembic_notes.md   # Migration development notes
├── migrations/            # Alembic migration files
│   ├── versions/          # Migration version files
│   ├── env.py             # Alembic environment configuration
│   └── script.py.mako     # Migration template
├── docker-compose.yml     # Docker orchestration
├── start_dev.bat          # Windows development script
├── start_dev.sh           # Linux/macOS development script
├── env.example            # Environment variables template
├── .env                   # Environment variables (create from env.example)
└── uploads/              # File uploads directory
```
 - **`app/`**: Main application code, templates, and database models
 - **`db_utils/`**: Database utility scripts
 - **`docs/`**: Documentation and development notes
 - **`migrations/`**: Alembic database migration files
 - **Root**: Configuration and orchestration files

## Database Schema

The application uses PostgreSQL with a well-structured schema designed for multi-project requirements management.

### Core Tables

#### **Users** (`users`)
- **Purpose**: User authentication and access control
- **Key Fields**:
  - `id` (UUID, Primary Key)
  - `username` (Unique, indexed)
  - `password_hash` (Encrypted)
  - `email` (Unique, nullable)
  - `is_active` (Boolean)
  - `created_at`, `updated_at` (Timestamps)

#### **Projects** (`projects`)
- **Purpose**: Highest-level classification for requirements
- **Key Fields**:
  - `id` (UUID, Primary Key)
  - `name` (Unique, indexed)
  - `description` (Text)
  - `created_by` (String)
  - `created_at`, `updated_at` (Timestamps)

#### **User-Project Access** (`user_projects`)
- **Purpose**: Many-to-many relationship for user access to projects
- **Key Fields**:
  - `user_id` (Foreign Key to users.id)
  - `project_id` (Foreign Key to projects.id)
  - **Composite Primary Key**: (user_id, project_id)

#### **Groups** (`groups`)
- **Purpose**: Hierarchical organization of requirements within projects
- **Key Fields**:
  - `id` (UUID, Primary Key)
  - `name` (Indexed, unique within project)
  - `description` (Text)
  - `parent_id` (Self-referencing foreign key for hierarchy)
  - `project_id` (Foreign Key to projects.id, CASCADE delete)
  - `created_at`, `updated_at` (Timestamps)

#### **Requirements** (`requirements`)
- **Purpose**: Core requirement data with project-scoped uniqueness
- **Key Fields**:
  - `id` (UUID, Primary Key)
  - `requirement_id` (String, unique within project)
  - `title` (String, required)
  - `description` (Text)
  - `status` (String: Draft, In Progress, Review, Completed, deleted)
  - `chapter` (String, nullable)
  - `verification_method` (String: A, RoD, I, T, nullable)
  - `group_id` (Foreign Key to groups.id, CASCADE delete)
  - `project_id` (Foreign Key to projects.id, CASCADE delete)
  - `created_by`, `updated_by` (String)
  - `graph_x`, `graph_y` (Float, for visual positioning)
  - `created_at`, `updated_at` (Timestamps)

#### **Requirement Relationships** (`requirement_links`)
- **Purpose**: Many-to-many parent-child relationships between requirements
- **Key Fields**:
  - `parent_id` (Foreign Key to requirements.id)
  - `child_id` (Foreign Key to requirements.id)
  - **Composite Primary Key**: (parent_id, child_id)

#### **Change History** (`cell_history`)
- **Purpose**: Audit trail for requirement field changes
- **Key Fields**:
  - `id` (Integer, Primary Key, Auto-increment)
  - `requirement_id` (Foreign Key to requirements.id)
  - `field_name` (String: title, description, status, chapter, verification_method, group_id)
  - `old_value`, `new_value` (Text)
  - `changed_by` (String)
  - `changed_at` (Timestamp)

### Key Constraints and Indexes

#### **Unique Constraints**
- **Users**: `username` (global), `email` (global)
- **Projects**: `name` (global)
- **Requirements**: `(requirement_id, project_id)` (project-scoped)
- **Groups**: `name` (project-scoped, enforced in application logic)

#### **Foreign Key Constraints**
- All foreign keys have CASCADE delete where appropriate
- **Groups**: `project_id` → `projects.id` (CASCADE)
- **Requirements**: `group_id` → `groups.id` (CASCADE)
- **Requirements**: `project_id` → `projects.id` (CASCADE)
- **Cell History**: `requirement_id` → `requirements.id` (CASCADE)

#### **Check Constraints**
- **Requirements**: `verification_method` must be NULL or one of: 'A', 'RoD', 'I', 'T'

#### **Indexes**
- **Performance**: All foreign keys and frequently queried fields are indexed
- **Hierarchy**: `groups.parent_id` for efficient tree traversal
- **Search**: `requirements.requirement_id`, `groups.name` for fast lookups

### Data Relationships

#### **Project Hierarchy**
```
Project (1) ←→ (Many) Groups
Project (1) ←→ (Many) Requirements
Project (Many) ←→ (Many) Users (via user_projects)
```

#### **Group Hierarchy**
```
Group (1) ←→ (Many) Groups (self-referencing parent_id)
Group (1) ←→ (Many) Requirements
```

#### **Requirement Relationships**
```
Requirement (Many) ←→ (Many) Requirements (via requirement_links)
Requirement (1) ←→ (Many) CellHistory (audit trail)
```

### Business Rules

#### **Access Control**
- Users can only access projects they're explicitly assigned to
- All operations are scoped to the user's accessible projects

#### **Data Integrity**
- **Soft Delete**: Requirements are marked as 'deleted' rather than physically removed
- **Project Scoping**: All data is isolated by project
- **Audit Trail**: All requirement changes are tracked in cell_history

#### **Validation Rules**
- **Verification Methods**: Only A (Analysis), RoD (Review of Design), I (Inspection), T (Test) allowed
- **Status Values**: Draft, In Progress, Review, Completed, deleted
- **Unique IDs**: requirement_id must be unique within a project

### Migration Management

The schema is managed through **Alembic migrations** with a clean baseline:
- **Current Baseline**: `clean_baseline` migration
- **Migration Files**: Located in `migrations/versions/`
- **Management**: Use `db_utils/manage_migrations.py` for all operations

### Schema Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     users       │    │   user_projects  │    │    projects     │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ id (PK)         │◄───┤ user_id (FK)     │    │ id (PK)         │
│ username (UQ)   │    │ project_id (FK)  │───►│ name (UQ)       │
│ password_hash   │    │ (PK: u_id+p_id)  │    │ description     │
│ email (UQ)      │    └──────────────────┘    │ created_by      │
│ is_active       │                            │ created_at      │
│ created_at      │                            │ updated_at      │
│ updated_at      │                            └─────────────────┘
└─────────────────┘                                      │
                                                         │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     groups      │    │  requirements   │    │ requirement_    │
├─────────────────┤    ├─────────────────┤    │    links        │
│ id (PK)         │◄───┤ id (PK)         │    ├─────────────────┤
│ name            │    │ requirement_id  │◄───┤ parent_id (FK)  │
│ description     │    │ title           │    │ child_id (FK)   │
│ parent_id (FK)  │    │ description     │    │ (PK: p_id+c_id) │
│ project_id (FK) │    │ status          │    └─────────────────┘
│ created_at      │    │ chapter         │
│ updated_at      │    │ verification_   │
└─────────────────┘    │   method        │    ┌─────────────────┐
                       │ group_id (FK)   │    │  cell_history   │
                       │ project_id (FK) │    ├─────────────────┤
                       │ created_by      │◄───┤ id (PK)         │
                       │ updated_by      │    │ requirement_id  │
                       │ graph_x         │    │ field_name      │
                       │ graph_y         │    │ old_value       │
                       │ created_at      │    │ new_value       │
                       │ updated_at      │    │ changed_by      │
                       └─────────────────┘    │ changed_at      │
                                              └─────────────────┘
```

**Legend:**
- **PK**: Primary Key
- **FK**: Foreign Key  
- **UQ**: Unique Constraint
- **◄───**: One-to-Many relationship
- **◄───►**: Many-to-Many relationship

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

# 2. Set up environment variables
cp env.example .env
# Edit .env file if needed

# 3. Start database service only
docker-compose up -d postgres

# 4. Apply database migrations
python db_utils/manage_migrations.py upgrade

# 5. Run Flask app locally
python -m app.app

# Access: http://localhost:5000
```

## Environment Variables

**Single Source of Truth**: All environment variables are managed through a `.env` file.

### Setup
1. Copy the template: `cp env.example .env`
2. Modify `.env` as needed for your environment
3. All scripts and Docker Compose will automatically use these variables

### Configuration
The `.env` file contains all necessary variables:
- **Database URLs**: Separate URLs for local and Docker environments
- **Flask Settings**: Environment, debug mode, host, port, secret key
- **PostgreSQL**: Database credentials and port for Docker
- **File Uploads**: Upload folder and size limits
- **Session**: Session type configuration

**Note**: Docker image versions (e.g., `python:3.11-slim`, `postgres:13-alpine`) are intentionally kept in Docker files as they are version-specific and don't need runtime configuration.

### How It Works
- **Local Development**: Scripts load variables from `.env`
- **Docker Compose**: Uses `env_file: .env` directive
- **Python App**: `load_dotenv()` reads `.env` automatically
- **Railway**: Set variables in Railway dashboard (no `.env` file needed)

### Example `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng


# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=dev-secret-key-change-in-production

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# PostgreSQL Configuration (for Docker)
POSTGRES_DB=reqmng
POSTGRES_USER=reqmng
POSTGRES_PASSWORD=reqmng
POSTGRES_PORT=5432

# Session Configuration
SESSION_TYPE=filesystem
```

## Development

### Local Development Setup
1. Use Method 2 (Hybrid Deployment)
2. Make changes to files in `app/` directory
3. Flask app auto-reloads on file changes
4. Database tables are auto-created on startup

### SQLAlchemy 2.0 Compatibility
The application uses modern SQLAlchemy 2.0 patterns:
- Uses `db.session.get(Model, id)` instead of deprecated `Model.query.get(id)`
- Compatible with Flask-SQLAlchemy 3.x
- No deprecation warnings

### Accessibility (a11y) Features
The application includes proper accessibility support:
- **Focus Management**: Proper focus restoration when modals close
- **ARIA Attributes**: Correct ARIA labels and descriptions for screen readers
- **Keyboard Navigation**: Full keyboard accessibility for all interactive elements
- **Screen Reader Support**: Semantic HTML and proper labeling

### Reset Everything
```bash
docker-compose down -v
docker-compose up --build
```

### Rebuild image
```bash
docker-compose up --build --force-recreate
```

## Database Migrations

This project uses **Alembic** for database schema management. All database changes should be made through migrations.

### How It Works

The migration system automatically:
1. **Reads** the current database version from `alembic_version` table
2. **Scans** available migrations in `migrations/versions/`
3. **Compares** database version vs. repository version
4. **Applies** any missing migrations in order
5. **Updates** the database version to latest

### Database Switching

**To work with any database, simply change `DATABASE_URL` in `.env`:**
```bash
# Local development
DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng

# Production (Railway)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Staging/Testing
DATABASE_URL=postgresql://user:pass@staging-host:5432/staging_db
```

**Then run the same migration commands:**
```bash
python db_utils/manage_migrations.py status    # Check status
python db_utils/manage_migrations.py upgrade   # Apply migrations
```

### Local Migration Commands

```bash
# Check migration status
python db_utils/manage_migrations.py status

# Create a new migration (after model changes)
python db_utils/manage_migrations.py create "Description of changes"

# Apply pending migrations
python db_utils/manage_migrations.py upgrade

# Rollback last migration
python db_utils/manage_migrations.py downgrade

# Show migration history
python db_utils/manage_migrations.py history

# Mark database as up-to-date (fix version mismatches)
python db_utils/manage_migrations.py stamp <version>

# Mark database as latest version (when schema is correct but version is wrong)
python db_utils/manage_migrations.py stamp head

### Migration Troubleshooting

**When migrations fail, the system will show diagnostic information and require manual intervention:**

1. **Check Migration Status**:
   ```bash
   python db_utils/manage_migrations.py status
   ```

2. **If Schema is Correct but Version is Wrong**:
   ```bash
   python db_utils/manage_migrations.py stamp head
   ```

3. **If Schema is Inconsistent**:
   - **Option A**: Reset database and reapply migrations
   - **Option B**: Manually fix schema inconsistencies
   - **Option C**: Create a new migration to fix the issue

4. **Common Issues**:
   - **DuplicateColumn**: Column already exists → Use `stamp head`
   - **MissingColumn**: Column doesn't exist → Apply migrations or fix schema
   - **VersionMismatch**: Database version tracking is wrong → Use `stamp <version>`

**⚠️ Important**: Never automatically stamp databases in production. Always investigate migration failures.
```

### Database Management

**Switch Between Databases:**
Simply change the `DATABASE_URL` in your `.env` file:

```bash
# Local development
DATABASE_URL=postgresql://reqmng:reqmng@localhost:5432/reqmng

# Production (Railway)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Any other database
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

**Apply Migrations to Any Database:**
```bash
# The same command works for any database
python db_utils/manage_migrations.py upgrade
```

### Migration Workflow

1. **Make model changes** in `app/models.py`
2. **Create migration**: `python db_utils/manage_migrations.py create "Description"`
3. **Review migration** in `migrations/versions/`
4. **Apply to any database**: `python db_utils/manage_migrations.py upgrade`
5. **Test changes** in your application
6. **Deploy to production**:
   - **Option A**: Commit and push to trigger Railway deployment (automatic)
   - **Option B**: Change `DATABASE_URL` to production and run: `python db_utils/manage_migrations.py upgrade`

### Important Notes

- **Never modify existing migrations** that have been applied to production
- **Always test migrations** on a copy of production data
- **Backup your database** before applying migrations
- **Review auto-generated migrations** before applying them
- **Switch databases safely** by changing `DATABASE_URL` in `.env`
- **One migration system** works for all databases (local, production, staging, etc.)

