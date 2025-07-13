#!/usr/bin/env python3
"""
Database initialization script for Docker setup
"""
import os
from dotenv import load_dotenv
from app import app, db

# Import models to ensure they are registered with SQLAlchemy
from models import Requirement, CellHistory, Group, ExcelUpload

# Load environment variables
load_dotenv()

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