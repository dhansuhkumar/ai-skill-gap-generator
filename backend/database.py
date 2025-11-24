# database.py
import os
import sys
import sqlite3

DB_NAME = os.path.join(os.path.dirname(__file__), "..", "users.db") # fallback to local file if not set
 # ✅ This must be at the top level

def init_db():
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

    conn.commit()
    conn.close()