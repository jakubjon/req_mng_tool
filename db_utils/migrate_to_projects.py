#!/usr/bin/env python3
"""
Database migration script to add project_id columns to existing tables
This script will:
1. Create a default project
2. Add project_id columns to groups and requirements tables
3. Associate existing data with the default project
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Project, Group, Requirement, User
from sqlalchemy import text

def migrate_to_projects():
    """Migrate existing database to support projects"""
    app = create_app()
    
    with app.app_context():
        print("Starting database migration to support projects...")
        
        # Check if projects table exists
        try:
            result = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"))
            projects_table_exists = result.scalar()
            
            if not projects_table_exists:
                print("Creating projects table...")
                db.create_all()
                print("Projects table created successfully!")
            else:
                print("Projects table already exists.")
        except Exception as e:
            print(f"Error checking projects table: {e}")
            return
        
        # Create default project if no projects exist
        default_project = Project.query.first()
        if not default_project:
            print("Creating default project...")
            default_project = Project(
                name="Default Project",
                description="Default project for existing data"
            )
            db.session.add(default_project)
            db.session.commit()
            print(f"Default project created with ID: {default_project.id}")
        else:
            print(f"Using existing project: {default_project.name}")
        
        # Check if groups table has project_id column
        try:
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'groups' AND column_name = 'project_id'
                )
            """))
            groups_has_project_id = result.scalar()
            
            if not groups_has_project_id:
                print("Adding project_id column to groups table...")
                db.session.execute(text("ALTER TABLE groups ADD COLUMN project_id VARCHAR(36)"))
                db.session.execute(text("UPDATE groups SET project_id = :project_id"), 
                                 {"project_id": default_project.id})
                db.session.execute(text("ALTER TABLE groups ALTER COLUMN project_id SET NOT NULL"))
                db.session.execute(text("CREATE INDEX ix_groups_project_id ON groups(project_id)"))
                db.session.commit()
                print("project_id column added to groups table successfully!")
            else:
                print("groups table already has project_id column.")
        except Exception as e:
            print(f"Error updating groups table: {e}")
            db.session.rollback()
            return
        
        # Check if requirements table has project_id column
        try:
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'requirements' AND column_name = 'project_id'
                )
            """))
            requirements_has_project_id = result.scalar()
            
            if not requirements_has_project_id:
                print("Adding project_id column to requirements table...")
                db.session.execute(text("ALTER TABLE requirements ADD COLUMN project_id VARCHAR(36)"))
                db.session.execute(text("UPDATE requirements SET project_id = :project_id"), 
                                 {"project_id": default_project.id})
                db.session.execute(text("ALTER TABLE requirements ALTER COLUMN project_id SET NOT NULL"))
                db.session.execute(text("CREATE INDEX ix_requirements_project_id ON requirements(project_id)"))
                db.session.commit()
                print("project_id column added to requirements table successfully!")
            else:
                print("requirements table already has project_id column.")
        except Exception as e:
            print(f"Error updating requirements table: {e}")
            db.session.rollback()
            return
        
        # Check if user_projects table exists
        try:
            result = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_projects')"))
            user_projects_exists = result.scalar()
            
            if not user_projects_exists:
                print("Creating user_projects association table...")
                db.session.execute(text("""
                    CREATE TABLE user_projects (
                        user_id VARCHAR(36) REFERENCES users(id),
                        project_id VARCHAR(36) REFERENCES projects(id),
                        PRIMARY KEY (user_id, project_id)
                    )
                """))
                db.session.commit()
                print("user_projects table created successfully!")
            else:
                print("user_projects table already exists.")
        except Exception as e:
            print(f"Error creating user_projects table: {e}")
            db.session.rollback()
            return
        
        # Associate all existing users with the default project
        try:
            users = User.query.all()
            for user in users:
                if default_project not in user.projects:
                    user.projects.append(default_project)
            db.session.commit()
            print(f"Associated {len(users)} users with default project.")
        except Exception as e:
            print(f"Error associating users with project: {e}")
            db.session.rollback()
            return
        
        print("Database migration completed successfully!")
        print(f"Default project: {default_project.name} (ID: {default_project.id})")
        print("All existing data has been associated with the default project.")

if __name__ == "__main__":
    migrate_to_projects() 