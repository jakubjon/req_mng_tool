from app import app, db
from models import Requirement, CellHistory, Group, ExcelUpload

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
            print("  - requirements (with priority and group_id)")
            print("  - cell_history")
            print("  - excel_uploads")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            raise

if __name__ == '__main__':
    reset_database() 