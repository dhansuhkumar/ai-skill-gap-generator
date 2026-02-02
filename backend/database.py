# database.py
"""
Centralized database configuration for SQLite.
Exports DB_NAME for consistent usage across all modules.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Centralized database path configuration
# Use DB_PATH environment variable, or default to users.db in backend directory
DB_NAME = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))

# Export for use in other modules
__all__ = ['DB_NAME', 'init_db']

def init_db():
    # If Supabase is configured, skip local SQLite initialization
    # If Supabase is configured, we might still need local DB for other tables (hybrid mode)
    # So we do NOT skip local SQLite init anymore.
    
    print(f"🔧 Initializing database at: {os.path.abspath(DB_NAME)}")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                role TEXT,
                skills TEXT,
                recommendations TEXT
            )
        ''')
        # Add missing tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                display_name TEXT,
                resume_parsed_json TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS profile_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                skill_id INTEGER,
                confidence INTEGER,
                source TEXT
            )
        ''')

        # Auth users table for login/registration
        c.execute('''
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TEXT
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ Database initialized successfully at: {os.path.abspath(DB_NAME)}")
        print(f"   Tables created: users, profiles, skills, profile_skills, auth_users")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        raise