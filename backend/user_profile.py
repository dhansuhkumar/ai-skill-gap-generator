# user_profile.py
import sqlite3
import json
from database import DB_NAME

def save_user_profile(user_id, role, skills, recommendations):
    skills_str = ','.join(skills)
    recommendations_str = json.dumps(recommendations)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('REPLACE INTO users (user_id, role, skills, recommendations) VALUES (?, ?, ?, ?)',
              (user_id, role, skills_str, recommendations_str))
    conn.commit()
    conn.close()
    return True

def get_user_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT role, skills, recommendations FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        role, skills_str, recommendations_str = row
        return {
            "user_id": user_id,
            "role": role,
            "skills": skills_str.split(','),
            "recommendations": json.loads(recommendations_str)
        }
    return None