import sqlite3
import os

DB_PATH = 'users.db'

def check_users():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, email, password_hash, created_at FROM auth_users")
        users = cur.fetchall()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user[0]}, Email: {user[1]}, Created: {user[3]}")
    except sqlite3.OperationalError as e:
        print(f"Error querying table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_users()
