#!/usr/bin/env python3
"""
Database reset script
Drops all tables and recreates them
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app
from app.db import db
from app.models import Requirement, CellHistory, Group

def reset_database():
    """Drop and recreate all database tables"""
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("✅ All tables dropped")
            
            # Create all tables with new schema
            db.create_all()
            print("✅ All tables recreated with new schema")
            
            # Create default group
            default_group = Group(
                name='Default',
                description='Default group for requirements'
            )
            db.session.add(default_group)
            db.session.commit()
            print("✅ Default group created")
            
            print("Tables created:")
            print("  - groups")
            print("  - requirements (with group_id, chapter)")
            print("  - cell_history")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            raise

if __name__ == '__main__':
    reset_database() 