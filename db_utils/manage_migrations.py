#!/usr/bin/env python3
"""
Migration Management Script for Requirements Management Tool

This script provides convenient commands for managing database migrations using Alembic.
"""

import os
import sys
import subprocess
from pathlib import Path

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv()

# Set default environment variables only if not already set
os.environ.setdefault('FLASK_ENV', 'development')

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        if result.stdout and result.stdout.strip():
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def show_help():
    """Show help information"""
    print("""
🔧 Migration Management Script

Usage: python db_utils/manage_migrations.py <command>

Commands:
  status      - Show current migration status
  history     - Show migration history
  create      - Create a new migration (provide description)
  upgrade     - Apply pending migrations
  downgrade   - Rollback last migration
  stamp       - Mark database as up-to-date with current migration
  current     - Show current migration version
  heads       - Show all head revisions

Examples:
  python db_utils/manage_migrations.py status
  python db_utils/manage_migrations.py create "Add new feature"
  python db_utils/manage_migrations.py upgrade
  python db_utils/manage_migrations.py downgrade
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    
    if command == "status":
        run_command("alembic current", "Checking migration status")
        run_command("alembic heads", "Checking head revisions")
        
    elif command == "history":
        run_command("alembic history", "Showing migration history")
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a description for the migration")
            print("Example: python db_utils/manage_migrations.py create 'Add new feature'")
            return
        description = sys.argv[2]
        run_command(f'alembic revision --autogenerate -m "{description}"', f"Creating migration: {description}")
        
    elif command == "upgrade":
        run_command("alembic upgrade head", "Applying pending migrations")
        
    elif command == "downgrade":
        run_command("alembic downgrade -1", "Rolling back last migration")
        
    elif command == "stamp":
        run_command("alembic stamp head", "Marking database as up-to-date")
        
    elif command == "current":
        run_command("alembic current", "Showing current migration version")
        
    elif command == "heads":
        run_command("alembic heads", "Showing all head revisions")
        
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main() 