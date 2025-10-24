# database.py
import sqlite3

DB_NAME = 'users.db'  # ✅ This must be at the top level

def init_db():
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