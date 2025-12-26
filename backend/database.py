# database.py
import os
import sys
import sqlite3

DB_NAME = os.path.join(os.path.dirname(__file__), "..", "users.db") # fallback to local file if not set

def init_db():
    # If Supabase is configured, skip local SQLite initialization
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        print("Supabase detected via env vars — skipping local SQLite init.")
        return

    print("Trying to open DB at:", DB_NAME)
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
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT
        )
    ''')

    conn.commit()
    conn.close()