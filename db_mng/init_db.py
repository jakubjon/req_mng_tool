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
from app.models import Requirement, CellHistory, Group, User

def init_database():
    """Initialize database with tables and sample data"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ All tables created")
            
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
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    init_database() 