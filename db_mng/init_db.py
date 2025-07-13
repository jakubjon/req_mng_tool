#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and adds sample data
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app
from app.db import db
from app.models import Requirement, CellHistory, Group

def init_database():
    """Initialize database tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Create default group if it doesn't exist
            default_group = Group.query.filter_by(name='Default').first()
            if not default_group:
                default_group = Group(
                    name='Default',
                    description='Default group for requirements'
                )
                db.session.add(default_group)
                db.session.commit()
                print("✅ Default group created")
            
            print("✅ Database tables created successfully")
            print("Tables created:")
            print("  - groups")
            print("  - requirements")
            print("  - cell_history")
            print("  - excel_uploads")
            
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            raise

if __name__ == "__main__":
    init_database() 