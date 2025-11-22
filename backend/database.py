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
    conn.commit()
    conn.close()