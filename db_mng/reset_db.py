#!/usr/bin/env python3
"""
Database reset script
Drops all tables and recreates them
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from db import db
from db.models import Requirement, CellHistory, Group, User

app = create_app()

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
            
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@example.com'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            db.session.commit()
            print("✅ Default group and admin user created")
            print("📝 Admin credentials: admin / admin123")
            
            print("Tables created:")
            print("  - users")
            print("  - groups")
            print("  - requirements (with group_id, chapter)")
            print("  - cell_history")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            raise

if __name__ == '__main__':
    reset_database() 
