import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = 'users.db'

def reset_password(email, new_password):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        password_hash = generate_password_hash(new_password)
        cur.execute("UPDATE auth_users SET password_hash = ? WHERE email = ?", (password_hash, email))
        if cur.rowcount > 0:
            print(f"Password for {email} reset to '{new_password}'.")
            conn.commit()
        else:
            print(f"User {email} not found.")
    except Exception as e:
        print(f"Error resetting password: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_password("dhanushindm@gmail.com", "password")
