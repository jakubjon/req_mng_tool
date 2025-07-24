#!/usr/bin/env python3
"""
Database migration script to fix requirement_id constraint
This script will:
1. Remove the global unique constraint on requirement_id
2. Ensure requirement_id is only unique within projects
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def fix_requirement_id_constraint():
    """Fix the requirement_id constraint to be project-scoped only"""
    app = create_app()
    
    with app.app_context():
        print("Starting requirement_id constraint fix...")
        
        try:
            # Check for unique indexes on requirement_id (global)
            result = db.session.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'requirements'
                AND indexname = 'ix_requirements_requirement_id'
                AND indexdef LIKE '%UNIQUE%'
            """))
            
            global_unique_index = result.fetchone()
            
            if global_unique_index:
                print(f"Found global unique index on requirement_id: {global_unique_index[0]}")
                print(f"Index definition: {global_unique_index[1]}")
                
                # Drop the global unique index
                print(f"Dropping index: {global_unique_index[0]}")
                db.session.execute(text(f"DROP INDEX IF EXISTS {global_unique_index[0]}"))
                db.session.commit()
                print("Global unique index removed successfully!")
            else:
                print("No global unique index found on requirement_id.")
            
            # Check if composite unique index already exists
            result = db.session.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'requirements'
                AND indexname = 'ix_requirements_requirement_id_project_id'
            """))
            
            composite_index_exists = result.fetchone()
            
            if not composite_index_exists:
                print("Creating composite unique index (requirement_id, project_id)...")
                
                # Create composite unique index
                db.session.execute(text("""
                    CREATE UNIQUE INDEX ix_requirements_requirement_id_project_id 
                    ON requirements (requirement_id, project_id)
                """))
                db.session.commit()
                print("Composite unique index created successfully!")
            else:
                print("Composite unique index already exists.")
            
            print("Requirement ID constraint fix completed successfully!")
            print("Now requirement_id is only unique within each project.")
            
        except Exception as e:
            print(f"Error fixing requirement_id constraint: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == "__main__":
    success = fix_requirement_id_constraint()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 