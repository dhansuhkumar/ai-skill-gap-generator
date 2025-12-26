# backend/run.py
import sys
import os
from dotenv import load_dotenv
from flask import request, jsonify
from pathlib import Path

# Ensure project root is on sys.path so package imports work when running this file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

load_dotenv()

# Import local backend bootstrap (database init) after adjusting sys.path
# Prefer Supabase when configured; otherwise initialize local SQLite
supabase_client = None
try:
    from backend.supabase_client import get_supabase
except Exception:
    try:
        from supabase_client import get_supabase
    except Exception:
        get_supabase = None

if get_supabase:
    try:
        supabase_client = get_supabase()
    except Exception:
        supabase_client = None

if not supabase_client:
    from backend.database import init_db
    init_db()
else:
    print("Using Supabase for persistence — local SQLite init skipped.")

# Use explicit package imports to avoid "No module named 'app'" when running as a module
from backend.app import create_app

app = create_app()

@app.after_request
def set_response_headers(response):
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    elif response.mimetype == 'text/html':
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

